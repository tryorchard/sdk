"""Table-driven check that each resource wrapper hits the right METHOD + PATH."""
import httpx
import pytest

from .conftest import make_orchard

UUID = "a31eba21-953b-4184-8ed7-5cf3bd062615"


def _run(call):
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["method"] = req.method
        seen["path"] = req.url.path
        seen["body"] = req.content.decode() if req.content else ""
        # minimal bodies the wrappers may index into
        return httpx.Response(200, json={"instances": [], "url": "/api/x", "uuid": UUID})

    o = make_orchard(handler)
    call(o)
    return seen


@pytest.mark.parametrize("call,method,path", [
    (lambda o: o.sandboxes.list(), "GET", "/api/instances"),
    (lambda o: o.sandboxes.create(platform="android", name="x"), "POST", "/api/instances/create"),
    (lambda o: o.sandbox(UUID) if False else o.sandboxes.get(UUID).start(), "POST", f"/api/sandboxes/{UUID}/start"),
    (lambda o: o.sandboxes.get(UUID).stop(), "POST", f"/api/sandboxes/{UUID}/stop"),
    (lambda o: o.sandboxes.get(UUID).get(), "GET", f"/api/sandboxes/{UUID}"),
    (lambda o: o.sandboxes.get(UUID).tag("t", "#112233"), "PATCH", f"/api/sandboxes/{UUID}"),
    (lambda o: o.sandboxes.get(UUID).apps.uninstall("com.x"), "POST", f"/api/sandboxes/{UUID}/apps/uninstall"),
    (lambda o: o.sandboxes.get(UUID).snapshots.create("s1"), "POST", f"/api/sandboxes/{UUID}/snapshots"),
    (lambda o: o.sandboxes.get(UUID).snapshots.restore("s1"), "POST", f"/api/sandboxes/{UUID}/snapshots/s1"),
    (lambda o: o.keys.list(), "GET", "/api/tokens"),
    (lambda o: o.keys.create("k", sandbox_uuids=[UUID], allowed_features=["logs"]), "POST", "/api/tokens"),
    (lambda o: o.templates.list(), "GET", "/api/templates"),
    (lambda o: o.snapshots.list(), "GET", "/api/snapshots"),
    (lambda o: o.catalog.android(), "GET", "/api/android/catalog"),
    (lambda o: o.jobs.list(), "GET", "/api/jobs"),
    (lambda o: o.team.get(), "GET", "/api/org"),
    (lambda o: o.team.members.list(), "GET", "/api/org/members"),
    (lambda o: o.remote.catalog(), "GET", "/api/remote/catalog"),
    (lambda o: o.remote.create("modal", "box"), "POST", "/api/remote/create"),
    (lambda o: o.remote.get(1), "GET", "/api/remote/1"),
    (lambda o: o.remote.start(1), "POST", "/api/remote/1/start"),
    (lambda o: o.remote.stop(1), "POST", "/api/remote/1/stop"),
    (lambda o: o.remote.delete(1), "DELETE", "/api/remote/1"),
    (lambda o: o.remote.metrics(1), "GET", "/api/remote/1/metrics"),
    (lambda o: o.remote.download(1, "/x/note.txt", local="/dev/null"), "GET", "/api/remote/1/files/download"),
    # input wrappers all POST the unified /control endpoint
    (lambda o: o.sandboxes.get(UUID).tap(1, 2), "POST", f"/api/sandboxes/{UUID}/control"),
    (lambda o: o.sandboxes.get(UUID).swipe(1, 2, 3, 4), "POST", f"/api/sandboxes/{UUID}/control"),
    (lambda o: o.sandboxes.get(UUID).key("home"), "POST", f"/api/sandboxes/{UUID}/control"),
    (lambda o: o.sandboxes.get(UUID).text("hi"), "POST", f"/api/sandboxes/{UUID}/control"),
    (lambda o: o.sandboxes.get(UUID).tap_text("Login"), "POST", f"/api/sandboxes/{UUID}/control"),
    (lambda o: o.sandboxes.get(UUID).launch("com.x"), "POST", f"/api/sandboxes/{UUID}/control"),
    (lambda o: o.sandboxes.get(UUID).launch_intent("com.x", ".Main"), "POST", f"/api/sandboxes/{UUID}/control"),
    # frida: status is a GET, everything else POSTs the same /frida endpoint
    (lambda o: o.sandboxes.get(UUID).frida.status(), "GET", f"/api/sandboxes/{UUID}/frida"),
    (lambda o: o.sandboxes.get(UUID).frida.install(), "POST", f"/api/sandboxes/{UUID}/frida"),
    (lambda o: o.sandboxes.get(UUID).frida.start(), "POST", f"/api/sandboxes/{UUID}/frida"),
    (lambda o: o.sandboxes.get(UUID).frida.stop(), "POST", f"/api/sandboxes/{UUID}/frida"),
    (lambda o: o.sandboxes.get(UUID).frida.verify("com.x"), "POST", f"/api/sandboxes/{UUID}/frida"),
    (lambda o: o.sandboxes.get(UUID).frida.inject("x", "com.x"), "POST", f"/api/sandboxes/{UUID}/frida"),
    # debugger (lldb): status is a GET, install/start POST the same /debugger endpoint
    (lambda o: o.sandboxes.get(UUID).debugger.status(), "GET", f"/api/sandboxes/{UUID}/debugger"),
    (lambda o: o.sandboxes.get(UUID).debugger.install(), "POST", f"/api/sandboxes/{UUID}/debugger"),
    (lambda o: o.sandboxes.get(UUID).debugger.start("com.x"), "POST", f"/api/sandboxes/{UUID}/debugger"),
])
def test_wrapper_routes(call, method, path):
    seen = _run(call)
    assert (seen["method"], seen["path"]) == (method, path)


@pytest.mark.parametrize("call,needle", [
    (lambda o: o.sandboxes.get(UUID).tap(540, 1200), '"action":"tap","x":540,"y":1200'),
    (lambda o: o.sandboxes.get(UUID).swipe(1, 2, 3, 4, ms=120),
     '"action":"swipe","x1":1,"y1":2,"x2":3,"y2":4,"ms":120'),
    (lambda o: o.sandboxes.get(UUID).key("back"), '"action":"key","name":"back"'),
    (lambda o: o.sandboxes.get(UUID).text("hello"), '"action":"text","text":"hello"'),
    (lambda o: o.sandboxes.get(UUID).tap_text("OK"), '"action":"tap_text","text":"OK"'),
    (lambda o: o.sandboxes.get(UUID).launch("com.x"), '"action":"launch","app":"com.x"'),
    (lambda o: o.sandboxes.get(UUID).launch_intent("com.x", ".Main", action="A", data="u://x",
                                                   extras={"k": "v"}),
     '"action":"launch_intent","package":"com.x","component":".Main",'
     '"intent_action":"A","data":"u://x","extras":{"k":"v"}'),
    (lambda o: o.sandboxes.get(UUID).frida.install(), '"action":"install"'),
    (lambda o: o.sandboxes.get(UUID).frida.verify("SpringBoard"),
     '"action":"verify","process":"SpringBoard"'),
    (lambda o: o.sandboxes.get(UUID).frida.inject("console.log(1)", "com.x", timeout=10),
     '"action":"inject","script":"console.log(1)","process":"com.x","timeout":10'),
    (lambda o: o.sandboxes.get(UUID).debugger.start("com.x"),
     '"action":"start","process":"com.x"'),
])
def test_input_bodies(call, needle):
    assert needle in _run(call)["body"]


def test_gdb_bridge_builds_ws_url():
    # LocalBridge builds its channel URL on construction (before .start()).
    o = make_orchard(lambda req: __import__("httpx").Response(200))
    b = o.sandboxes.get(UUID).gdb_bridge(port=0)
    assert f"/ws/sandboxes/{UUID}/gdb" in b._url


def test_frida_stream_builds_ws_url():
    # SyncChannel does not connect on construction, so the URL is safe to inspect.
    o = make_orchard(lambda req: __import__("httpx").Response(200))
    ch = o.sandboxes.get(UUID).frida.stream("console.log(1)", "com.x", timeout=5)
    assert f"/ws/sandboxes/{UUID}/frida/stream" in ch._url
    assert "process=com.x" in ch._url and "timeout=5" in ch._url
    assert ch._open_send == "console.log(1)"   # script sent on connect


def test_key_create_sends_scope():
    seen = _run(lambda o: o.keys.create("k", sandbox_uuids=["u1"], tag="pay",
                                         allowed_features=["logs", "files"]))
    assert '"sandbox_uuids":["u1"]' in seen["body"]
    assert '"capabilities":["logs","files"]' in seen["body"]
    assert '"tag":"pay"' in seen["body"]


def test_webrtc_player_url_builds_ws_suffix():
    import httpx
    o = make_orchard(lambda r: httpx.Response(200, json={}))
    url = o.sandboxes.get(UUID).webrtc_player_url()
    assert "screen/webrtc" in url and "token=" in url
