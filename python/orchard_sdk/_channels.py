"""Synchronous wrappers over the async WebSocket core.

:class:`SyncChannel` lets ordinary (non-asyncio) code consume a live channel as
a plain iterator::

    with sandbox.logs() as stream:
        for line in stream:
            print(line)

It runs a private asyncio loop on a daemon thread, pushes decoded frames onto a
queue, and shuts the loop down cleanly when the ``with`` block exits — including
on ``break`` or Ctrl-C. :class:`Tunnel` drives the reverse-tunnel control channel.
"""
from __future__ import annotations

import asyncio
import json
import threading
from queue import Queue
from typing import Any, Callable, Iterator

from . import _ws
from .config import Config

_SENTINEL = object()


class SyncChannel:
    """A live WebSocket channel exposed as a context-managed, synchronous iterator.

    Args:
        url: The fully-built channel URL (see :func:`orchard_sdk._ws.ws_url`).
        decode: Per-frame decoder (text/json/bytes). Defaults to text.

    The channel is lazy: the socket opens on ``__enter__`` and closes on
    ``__exit__``. Iterating yields decoded frames until the stream ends or the
    block is left. ``send()`` pushes data upstream (e.g. shell keystrokes).
    """

    def __init__(self, url: str, decode: Callable[[str | bytes], Any] = _ws.decode_text,
                 queue_max: int = 0, open_send: str | bytes | None = None):
        self._url = url
        self._decode = decode
        self._open_send = open_send
        self._queue: "Queue[Any]" = Queue(maxsize=queue_max)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ws: Any = None
        self._stop = False
        self._exc: BaseException | None = None

    # -- lifecycle --------------------------------------------------------
    def __enter__(self) -> "SyncChannel":
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._pump())
        except BaseException as e:  # surfaced to the consumer thread via the queue
            self._exc = e
        finally:
            self._queue.put(_SENTINEL)
            self._loop.close()

    async def _pump(self) -> None:
        async with _ws.connect(self._url) as ws:
            self._ws = ws
            if self._open_send is not None:   # e.g. a frida script sent on connect
                await ws.send(self._open_send)
            try:
                async for frame in ws:
                    if self._stop:
                        break
                    self._queue.put(self._decode(frame))
            except Exception as e:  # ConnectionClosed w/ error code → re-raised to consumer
                import websockets
                if isinstance(e, websockets.ConnectionClosed):
                    err = _ws._closed_err(e)
                    if err is not None:
                        raise err from None
                elif not self._stop:
                    raise

    # -- consumer API -----------------------------------------------------
    def __iter__(self) -> Iterator[Any]:
        while True:
            item = self._queue.get()
            if item is _SENTINEL:
                if self._exc is not None:
                    raise self._exc
                return
            yield item

    def send(self, data: str | bytes) -> None:
        """Send a frame upstream (e.g. a shell keystroke or a resize JSON)."""
        if self._loop is None or self._ws is None:
            raise RuntimeError("channel not open")
        fut = asyncio.run_coroutine_threadsafe(self._ws.send(data), self._loop)
        fut.result(timeout=10)

    def close(self) -> None:
        """Stop the stream and join the worker thread."""
        self._stop = True
        if self._ws is not None and self._loop is not None and self._loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop).result(timeout=5)
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=5)


class Tunnel:
    """The reverse-tunnel control channel: forwards guest proxy connections into a
    local proxy you run (Burp/mitmproxy). Context-managed; blocks in :meth:`run`.
    """

    def __init__(self, cfg: Config, uuid: str, to_host: str, to_port: int):
        self._cfg = cfg
        self._uuid = uuid
        self._to = (to_host, to_port)

    def run(self, on_event: Callable[[str, str], None] | None = None) -> int:
        """Hold the tunnel open until the server closes it. ``on_event(level, text)``
        receives ``ready``/``open``/``warn``/``error``/``close`` notifications."""
        log = on_event or (lambda level, text: None)
        return asyncio.run(self._run(log))

    async def _run(self, log: Callable[[str, str], None]) -> int:
        tasks: set[asyncio.Task] = set()
        to_host, to_port = self._to

        async def data(sid: str) -> None:
            try:
                async with _ws.connect(_ws.ws_url(self._cfg, self._uuid, "tunnel/data", sid=sid)) as ws:
                    reader, writer = await asyncio.open_connection(to_host, to_port)
                    await _pump(ws, reader, writer)
            except Exception as e:
                log("warn", f"stream {sid[:8]} ended: {e}")

        async with _ws.connect(_ws.ws_url(self._cfg, self._uuid, "tunnel")) as control:
            async for raw in control:
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                t = msg.get("t")
                if t == "ready":
                    log("ready", f"guest proxy -> {msg.get('proxy_target')}")
                elif t == "open":
                    task = asyncio.create_task(data(msg["sid"]))
                    tasks.add(task)
                    task.add_done_callback(tasks.discard)
                elif t == "warn":
                    log("warn", msg.get("detail", ""))
                elif t == "error":
                    log("error", msg.get("detail", "tunnel refused"))
                    return 1
                elif t == "close":
                    log("close", "closed by server")
                    return 0
        return 0


async def _pump(ws: Any, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    async def to_ws() -> None:
        try:
            while chunk := await reader.read(65536):
                await ws.send(chunk)
        finally:
            await ws.close()

    async def to_local() -> None:
        try:
            async for msg in ws:
                writer.write(msg if isinstance(msg, (bytes, bytearray)) else msg.encode())
                await writer.drain()
        finally:
            try:
                writer.close()
            except Exception:
                pass

    await asyncio.gather(to_ws(), to_local(), return_exceptions=True)
