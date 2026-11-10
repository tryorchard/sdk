"""A local TCP listener bridged to a device WebSocket channel (adb, vnc, screen).

This lets ordinary local tools reach a sandbox as if it were plugged in: the
bridge opens a port and, for each TCP connection, opens a fresh channel to the
device and pumps bytes both ways. So ``adb connect 127.0.0.1:<port>`` talks to
the sandbox's adb, and a VNC viewer to its screen.

It runs its own asyncio loop on a daemon thread, like :class:`SyncChannel`.
"""
from __future__ import annotations

import asyncio
import threading
from typing import Any

from . import _ws
from .config import Config


class LocalBridge:
    """A local ``host:port`` listener forwarding to a device channel. Start it
    (or use it as a context manager); read :attr:`port`; :meth:`close` when done.

    >>> with sandbox.adb_bridge() as b:
    ...     os.system(f"adb connect 127.0.0.1:{b.port}")
    """

    def __init__(self, cfg: Config, uuid: str, suffix: str, host: str = "127.0.0.1",
                 port: int = 0, **params: Any):
        self._url = _ws.ws_url(cfg, uuid, suffix, **params)
        self.host = host
        self._req_port = port
        #: The bound local port (set once started; the OS picks one if port was 0).
        self.port = 0
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._server: asyncio.AbstractServer | None = None
        self._ready = threading.Event()
        self._err: BaseException | None = None

    def start(self) -> "LocalBridge":
        """Open the listener and return self once it is bound."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=15):
            raise RuntimeError("bridge did not start within 15s")
        if self._err is not None:
            raise self._err
        return self

    def __enter__(self) -> "LocalBridge":
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except BaseException as e:   # surfaced to start() via _ready/_err
            self._err = e
            self._ready.set()
        finally:
            self._loop.close()

    async def _serve(self) -> None:
        self._server = await asyncio.start_server(self._handle, self.host, self._req_port)
        self.port = self._server.sockets[0].getsockname()[1]
        self._ready.set()
        async with self._server:
            await self._server.serve_forever()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            async with _ws.connect(self._url) as ws:
                await self._pump(ws, reader, writer)
        except Exception:
            with _suppress():
                writer.close()

    @staticmethod
    async def _pump(ws: Any, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        async def to_ws() -> None:
            try:
                while chunk := await reader.read(65536):
                    await ws.send(chunk)
            except Exception:
                pass
            finally:
                with _suppress():
                    await ws.close()

        async def to_local() -> None:
            try:
                async for msg in ws:
                    writer.write(msg if isinstance(msg, (bytes, bytearray)) else msg.encode())
                    await writer.drain()
            except Exception:
                pass
            finally:
                with _suppress():
                    writer.close()

        await asyncio.gather(to_ws(), to_local(), return_exceptions=True)

    def close(self) -> None:
        """Stop the listener and join the worker thread."""
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=5)


class _suppress:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *exc: object) -> bool:
        return True   # swallow any exception in the with-body
