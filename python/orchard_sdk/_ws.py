"""Async WebSocket core: URL assembly + a decoded frame iterator.

A *channel* is one of Orchard's per-sandbox WebSocket streams (logs, shell,
screen, adb, vnc, mitm, …). Frames arrive as text or binary depending on the
channel; :func:`channel` decodes each frame with the caller-supplied ``decode``.
Used directly by :mod:`orchard_sdk.aio`; :mod:`orchard_sdk._channels` wraps it
for synchronous callers.
"""
from __future__ import annotations

import json as _json
from typing import Any, AsyncIterator, Callable
from urllib.parse import urlencode

import websockets

from .config import Config
from .errors import ChannelClosedError

# Close codes the control plane emits.
_ERR_CODES = {4401, 4403, 4404, 4502}


def _closed_err(exc: "websockets.ConnectionClosed") -> ChannelClosedError | None:
    """Map a ConnectionClosed to a ChannelClosedError when the code is an Orchard
    error code, else None (a normal end-of-stream). Reads the close frame
    directly to avoid the deprecated ``.code``/``.reason`` shims."""
    frame = getattr(exc, "rcvd", None) or getattr(exc, "sent", None)
    code = frame.code if frame is not None else 1006
    if code in _ERR_CODES:
        return ChannelClosedError(code, (frame.reason if frame is not None else "") or "")
    return None


def ws_url(cfg: Config, uuid: str, suffix: str, **extra: Any) -> str:
    """Build ``wss?://host/ws/sandboxes/<uuid>/<suffix>?token=…`` with auth + extras.

    ``extra`` values that are ``None`` are omitted (e.g. ``sid=None``).
    """
    q: dict[str, Any] = {"token": cfg.token}
    if cfg.org:
        q["org"] = cfg.org
    if cfg.ws:
        q["ws"] = cfg.ws
    q.update({k: v for k, v in extra.items() if v is not None})
    return f"{cfg.ws_base}/ws/sandboxes/{uuid}/{suffix}?{urlencode(q)}"


def raw_ws_url(cfg: Config, path: str, **extra: Any) -> str:
    """Build a WS URL for a non-sandbox path (e.g. ``ws/jobs/…``, ``ws/remote/…``)."""
    q: dict[str, Any] = {"token": cfg.token}
    if cfg.org:
        q["org"] = cfg.org
    if cfg.ws:
        q["ws"] = cfg.ws
    q.update({k: v for k, v in extra.items() if v is not None})
    return f"{cfg.ws_base}/{path.lstrip('/')}?{urlencode(q)}"


def connect(url: str):
    """Open a client connection with the raw-transport settings binary channels need."""
    return websockets.connect(url, max_size=None, open_timeout=15)


def decode_text(frame: str | bytes) -> str:
    return frame if isinstance(frame, str) else frame.decode(errors="replace")


def decode_json(frame: str | bytes) -> Any:
    return _json.loads(frame)


def decode_bytes(frame: str | bytes) -> bytes:
    return frame if isinstance(frame, (bytes, bytearray)) else frame.encode()


async def channel(url: str, decode: Callable[[str | bytes], Any] = decode_text
                  ) -> AsyncIterator[Any]:
    """Async-iterate decoded frames from ``url`` until the socket closes cleanly.

    Raises :class:`ChannelClosedError` if the server closes with an error code
    (4401/4403/4404/4502).
    """
    async with connect(url) as ws:
        try:
            async for frame in ws:
                yield decode(frame)
        except websockets.ConnectionClosed as exc:
            err = _closed_err(exc)
            if err is not None:
                raise err from None
            # 1000/1001/etc. are a normal end-of-stream.
