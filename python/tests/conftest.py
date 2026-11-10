"""Shared test fixtures: a MockTransport-backed Orchard client and a fake WS."""
from __future__ import annotations

from typing import Any, Callable

import httpx
import pytest

from orchard_sdk import Orchard


def make_orchard(handler: Callable[[httpx.Request], httpx.Response]) -> Orchard:
    """An Orchard whose REST transport is an httpx MockTransport running ``handler``."""
    o = Orchard("https://orchard.test", "orc_test", org="acme", ws="default")
    cfg = o.config
    headers = {"Authorization": f"Bearer {cfg.token}",
               "X-Orchard-Org": "acme", "X-Orchard-Workspace": "default"}
    o._http._c.close()
    o._http._c = httpx.Client(base_url=cfg.api_base, headers=headers,
                              transport=httpx.MockTransport(handler))
    return o


@pytest.fixture
def record():
    """A handler factory that records requests and returns canned JSON."""
    calls: list[httpx.Request] = []

    def factory(json_body: Any = None, status: int = 200, content: bytes | None = None):
        def handler(req: httpx.Request) -> httpx.Response:
            calls.append(req)
            if content is not None:
                return httpx.Response(status, content=content)
            return httpx.Response(status, json=json_body if json_body is not None else {})
        return handler

    factory.calls = calls  # type: ignore[attr-defined]
    return factory


class FakeWS:
    """An async WebSocket stand-in: yields ``frames`` then closes with ``code``."""

    def __init__(self, frames: list[Any], code: int = 1000, reason: str = ""):
        self._frames = list(frames)
        self._code = code
        self._reason = reason
        self.sent: list[Any] = []
        self.closed = False

    async def __aenter__(self) -> "FakeWS":
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    def __aiter__(self) -> "FakeWS":
        return self

    async def __anext__(self) -> Any:
        if self._frames:
            return self._frames.pop(0)
        if self._code not in (1000, 1001):
            import websockets
            from websockets.frames import Close
            raise websockets.ConnectionClosed(Close(self._code, self._reason), None)
        raise StopAsyncIteration

    async def send(self, data: Any) -> None:
        self.sent.append(data)

    async def close(self) -> None:
        self.closed = True
