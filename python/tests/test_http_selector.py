import httpx
import pytest

from orchard_sdk import ApiError, SelectorError
from orchard_sdk.selector import resolve, resolve_all

from .conftest import make_orchard

INSTANCES = [
    {"uuid": "a31eba21-953b-4184-8ed7-5cf3bd062615", "name": "cuttlefish",
     "display_name": "cuttlefish", "tag": "pay", "node": "droid"},
    {"uuid": "2609ff67-aaaa", "name": "pixel", "display_name": "pixel", "tag": "pay"},
    {"uuid": "6acc3ef4", "name": "spare", "tag": ""},
    {"name": "remote-x", "uuid": None, "tag": ""},
]


# --- transport ---
def test_headers_and_json(record):
    o = make_orchard(record({"username": "admin"}))
    assert o.me() == {"username": "admin"}
    req = record.calls[-1]
    assert req.headers["Authorization"] == "Bearer orc_test"
    assert req.headers["X-Orchard-Org"] == "acme"
    assert str(req.url).endswith("/api/me")


@pytest.mark.parametrize("status,needle", [
    (401, "invalid or expired"),
    (404, "no such sandbox"),
])
def test_error_mapping(record, status, needle):
    o = make_orchard(record(status=status, content=b""))   # empty body → fallback message
    with pytest.raises(ApiError) as e:
        o.me()
    assert needle in e.value.user_message


def test_delete_204_returns_none(record):
    o = make_orchard(record(status=204))
    assert o.keys.delete(5) is None


# --- selector ---
def test_selector_precedence():
    assert resolve(INSTANCES, "a31eba21-953b-4184-8ed7-5cf3bd062615")["name"] == "cuttlefish"
    assert resolve(INSTANCES, "6acc3ef4")["name"] == "spare"          # exact uuid short
    assert resolve(INSTANCES, "spare")["uuid"] == "6acc3ef4"          # name
    with pytest.raises(SelectorError):
        resolve(INSTANCES, "pay")                                     # tag → 2 matches
    assert len(resolve_all(INSTANCES, "pay")) == 2
    assert resolve_all(INSTANCES, "remote-x") == []                  # no-uuid excluded
    with pytest.raises(SelectorError):
        resolve(INSTANCES, "nope")
