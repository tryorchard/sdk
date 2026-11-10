from urllib.parse import parse_qs, urlsplit

import pytest

from orchard_sdk import ChannelClosedError, Config
from orchard_sdk import _ws
from orchard_sdk._channels import SyncChannel

from .conftest import FakeWS

CFG = Config("https://h.example", "orc_k", org="acme", ws="default")


def test_ws_url_carries_auth_and_extra():
    url = _ws.ws_url(CFG, "UU", "screen/stream", source="scrcpy")
    p = urlsplit(url)
    assert p.scheme == "wss" and p.netloc == "h.example"
    assert p.path == "/ws/sandboxes/UU/screen/stream"
    q = parse_qs(p.query)
    assert q["token"] == ["orc_k"] and q["org"] == ["acme"]
    assert q["ws"] == ["default"] and q["source"] == ["scrcpy"]


def test_ws_url_omits_none_extra():
    q = parse_qs(urlsplit(_ws.ws_url(CFG, "U", "adb", sid=None)).query)
    assert "sid" not in q


def test_sync_channel_yields_then_closes(monkeypatch):
    monkeypatch.setattr(_ws, "connect", lambda url: FakeWS(["a", "b", "c"]))
    with SyncChannel(_ws.ws_url(CFG, "U", "logs"), _ws.decode_text) as ch:
        assert list(ch) == ["a", "b", "c"]


def test_sync_channel_decodes_bytes(monkeypatch):
    monkeypatch.setattr(_ws, "connect", lambda url: FakeWS([b"\x00\x01", "x"]))
    with SyncChannel(_ws.ws_url(CFG, "U", "screen/stream"), _ws.decode_bytes) as ch:
        out = list(ch)
    assert out == [b"\x00\x01", b"x"]


def test_sync_channel_error_code_raises(monkeypatch):
    monkeypatch.setattr(_ws, "connect", lambda url: FakeWS([], code=4403, reason="forbidden"))
    with pytest.raises(ChannelClosedError) as e:
        with SyncChannel(_ws.ws_url(CFG, "U", "logs")) as ch:
            list(ch)
    assert e.value.code == 4403


@pytest.mark.asyncio
async def test_async_channel(monkeypatch):
    monkeypatch.setattr(_ws, "connect", lambda url: FakeWS(["l1", "l2"]))
    got = [f async for f in _ws.channel(_ws.ws_url(CFG, "U", "logs"), _ws.decode_text)]
    assert got == ["l1", "l2"]
