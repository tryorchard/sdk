"""Async WebSocket channels for asyncio callers.

The synchronous :class:`orchard_sdk.resources.sandboxes.Sandbox` channels wrap
these behind a thread. If you are already in an event loop, use these directly::

    import asyncio
    from orchard_sdk import from_env
    from orchard_sdk.aio import AsyncChannels

    async def main():
        cfg = from_env()
        async for line in AsyncChannels(cfg, "<uuid>").logs():
            print(line)

    asyncio.run(main())
"""
from __future__ import annotations

from typing import Any, AsyncIterator

from .. import _ws
from ..config import Config


class AsyncChannels:
    """Async-iterable live channels for one sandbox uuid."""

    def __init__(self, cfg: Config, uuid: str):
        self._cfg = cfg
        self._uuid = uuid

    def _url(self, suffix: str, **extra: Any) -> str:
        return _ws.ws_url(self._cfg, self._uuid, suffix, **extra)

    def logs(self) -> AsyncIterator[str]:
        """Async-iterate log lines."""
        return _ws.channel(self._url("logs"), _ws.decode_text)

    def shell(self) -> AsyncIterator[str]:
        """Async-iterate shell output (read-only here; use the raw socket to send)."""
        return _ws.channel(self._url("shell"), _ws.decode_text)

    def screen(self, source: str = "scrcpy") -> AsyncIterator[bytes]:
        """Async-iterate raw screen frames."""
        return _ws.channel(self._url("screen/stream", source=source), _ws.decode_bytes)

    def adb(self) -> AsyncIterator[bytes]:
        """Async-iterate raw adb transport bytes."""
        return _ws.channel(self._url("adb"), _ws.decode_bytes)

    def vnc(self) -> AsyncIterator[bytes]:
        """Async-iterate raw RFB bytes (iOS VM)."""
        return _ws.channel(self._url("vnc"), _ws.decode_bytes)

    def mitm_flows(self) -> AsyncIterator[Any]:
        """Async-iterate captured flow summaries (decoded JSON)."""
        return _ws.channel(self._url("mitm/flows"), _ws.decode_json)
