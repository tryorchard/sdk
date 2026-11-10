import pytest

from orchard_sdk import Config, from_env


def test_api_and_ws_base():
    c = Config("https://h.example/x", "orc_k")
    assert c.api_base == "https://h.example/x/api"
    assert c.ws_base == "wss://h.example"
    assert Config("http://h:8000", "t").ws_base == "ws://h:8000"


def test_from_env_flag_beats_env(monkeypatch):
    monkeypatch.setenv("ORCHARD_API_URL", "https://env")
    monkeypatch.setenv("ORCHARD_API_KEY", "orc_env")
    c = from_env("https://flag", "orc_flag")
    assert (c.url, c.token) == ("https://flag", "orc_flag")


def test_from_env_legacy_url_alias(monkeypatch):
    monkeypatch.delenv("ORCHARD_API_URL", raising=False)
    monkeypatch.setenv("ORCHARD_URL", "https://legacy")
    monkeypatch.setenv("ORCHARD_API_KEY", "orc_x")
    assert from_env().url == "https://legacy"


def test_from_env_missing_raises(monkeypatch):
    for k in ("ORCHARD_API_URL", "ORCHARD_URL", "ORCHARD_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(ValueError):
        from_env()
