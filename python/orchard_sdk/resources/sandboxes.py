"""Sandboxes: listing/creating them, and the :class:`Sandbox` handle that drives
one sandbox (lifecycle, editing, files, apps, snapshots, and live channels)."""
from __future__ import annotations

from pathlib import Path
from typing import List, Any, cast

from .. import _ws
from .._bridge import LocalBridge
from .._channels import SyncChannel, Tunnel
from .._http import HttpClient
from ..config import Config
from ..models import Instance, InstanceList, SnapshotRow
from ..selector import resolve, resolve_all


class Sandboxes:
    """The ``orchard.sandboxes`` namespace: fleet-wide listing and creation."""

    def __init__(self, http: HttpClient, cfg: Config):
        self._http = http
        self._cfg = cfg

    def list(self) -> InstanceList:
        """List every sandbox visible to this key/org.

        >>> for s in orchard.sandboxes.list()["instances"]:
        ...     print(s["name"], s["state"])
        """
        return self._http.get("/instances")

    def create(self, **spec: Any) -> dict[str, Any]:
        """Create a sandbox. ``spec`` includes ``platform`` ("ios"/"android"),
        ``name``, ``cpu``, ``memory_mb``, and platform fields (``image``/``device``
        for Android, ``preset``/``variant`` for iOS)."""
        return self._http.post("/instances/create", json=spec)

    def create_sim(self, **spec: Any) -> dict[str, Any]:
        """Create an iOS simulator sandbox (``name``, ``device_type``, ``runtime``)."""
        return self._http.post("/instances/create-sim", json=spec)

    def resolve(self, selector: str) -> Instance:
        """Resolve a selector (uuid / uuid-prefix / name / tag) to one instance dict."""
        return cast(Instance, resolve(list(self.list()["instances"]), selector))

    def resolve_all(self, selector: str) -> List[Instance]:
        """Every instance a selector matches (tags match many)."""
        return cast("List[Instance]", resolve_all(list(self.list()["instances"]), selector))

    def get(self, uuid: str) -> "Sandbox":
        """A :class:`Sandbox` handle for a known uuid (no lookup)."""
        return Sandbox(self._http, self._cfg, uuid)


class Sandbox:
    """A handle to one sandbox, addressed by uuid. Returned by
    ``orchard.sandbox(selector)`` and ``orchard.sandboxes.get(uuid)``."""

    def __init__(self, http: HttpClient, cfg: Config, uuid: str):
        self._http = http
        self._cfg = cfg
        self.uuid = uuid
        self._base = f"/sandboxes/{uuid}"
        self.files = Files(http, cfg, uuid)
        self.apps = Apps(http, cfg, uuid)
        self.snapshots = SandboxSnapshots(http, uuid)
        self.frida = Frida(http, cfg, uuid)
        self.debugger = Debugger(http, cfg, uuid)

    # -- lifecycle --------------------------------------------------------
    def get(self) -> Instance:
        """Fetch the full current instance dict."""
        return self._http.get(self._base)

    def start(self) -> dict[str, Any]:
        """Start (boot) the sandbox."""
        return self._http.post(f"{self._base}/start")

    def stop(self) -> dict[str, Any]:
        """Stop the sandbox."""
        return self._http.post(f"{self._base}/stop")

    def delete(self) -> dict[str, Any]:
        """Terminate the sandbox (deletes its disk on the node)."""
        return self._http.delete(self._base)

    def edit(self, *, notes: str | None = None, tag: str | None = None,
             tag_color: str | None = None, owner: str | None = None,
             cpu: int | None = None, memory_mb: int | None = None) -> Instance:
        """Change metadata/size. ``cpu``/``memory_mb`` require the sandbox stopped;
        ``owner`` requires org-admin."""
        body = {k: v for k, v in dict(notes=notes, tag=tag, tag_color=tag_color,
                                      owner=owner, cpu=cpu, memory_mb=memory_mb).items()
                if v is not None}
        if not body:
            raise ValueError("edit() needs at least one field")
        return self._http.patch(self._base, json=body)

    def tag(self, tag: str, color: str | None = None) -> Instance:
        """Set the sandbox's tag (and optional ``#rrggbb`` chip color)."""
        body: dict[str, Any] = {"tag": tag}
        if color is not None:
            body["tag_color"] = color
        return self._http.patch(self._base, json=body)

    # -- input / inspection ----------------------------------------------
    def control(self, action: str, **kw: Any) -> dict[str, Any]:
        """Send a unified input action (``tap``/``swipe``/``key``/``text``/``launch``/``tap_text``)."""
        return self._http.post(f"{self._base}/control", json={"action": action, **kw})

    def tap(self, x: int, y: int) -> dict[str, Any]:
        """Tap (click) at device pixel coordinates ``(x, y)``."""
        return self.control("tap", x=int(x), y=int(y))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, ms: int = 300) -> dict[str, Any]:
        """Swipe/drag from ``(x1, y1)`` to ``(x2, y2)`` over ``ms`` milliseconds."""
        return self.control("swipe", x1=int(x1), y1=int(y1), x2=int(x2), y2=int(y2), ms=int(ms))

    def key(self, name: str) -> dict[str, Any]:
        """Press a hardware/navigation key (e.g. ``home``, ``back``, ``enter``, ``power``)."""
        return self.control("key", name=name)

    def text(self, text: str) -> dict[str, Any]:
        """Type ``text`` into the focused field."""
        return self.control("text", text=text)

    #: Alias of :meth:`text`, for callers who prefer the verb.
    type_text = text

    def tap_text(self, text: str) -> dict[str, Any]:
        """Find an on-screen element whose label matches ``text`` and tap it."""
        return self.control("tap_text", text=text)

    def launch(self, app: str) -> dict[str, Any]:
        """Launch an app by package id (Android) or bundle id (iOS)."""
        return self.control("launch", app=app)

    def launch_intent(self, package: str, component: str, *, action: str | None = None,
                      data: str | None = None, extras: dict[str, str] | None = None) -> dict[str, Any]:
        """Start an exported activity ``component`` in ``package`` (Android), with
        an optional intent ``action``, ``data`` URI and string ``extras``. The
        activity must be exported, or the device refuses the launch."""
        body: dict[str, Any] = {"package": package, "component": component}
        if action is not None:
            body["intent_action"] = action
        if data is not None:
            body["data"] = data
        if extras is not None:
            body["extras"] = extras
        return self.control("launch_intent", **body)

    def screenshot(self) -> bytes:
        """A PNG/JPEG screenshot (raw bytes)."""
        return self._http.get_content(f"{self._base}/screenshot")

    def describe_ui(self) -> dict[str, Any]:
        """The accessibility/UI tree."""
        return self._http.get(f"{self._base}/describe-ui")

    def metrics(self) -> dict[str, Any]:
        """Live CPU/memory/battery/uptime metrics."""
        return self._http.get(f"{self._base}/metrics")

    def storage(self) -> dict[str, Any]:
        """Disk-usage breakdown (apps/media/system/free)."""
        return self._http.get(f"{self._base}/storage")

    def export_avd(self, dest: str | Path, *, timeout: float = 7200.0) -> dict[str, Any]:
        """Export this Android sandbox's AVD as a portable profile ``.tar`` to ``dest``,
        for sharing or for :meth:`Templates.import_avd` onto another node. **Stop the
        device first** (a profile is copied at rest). The profile holds the disk images
        and a manifest naming the system image it needs — not the base image itself.

        Returns the profile metadata (``filename``, ``size_bytes``, ``system_image``, …)
        plus ``saved_to`` and ``bytes``.
        """
        dest = Path(dest)
        meta = self._http.post(f"{self._base}/avd/export")
        got = self._http.stream_to_file(
            f"{self._base}/avd/export/{meta['filename']}", dest, timeout=timeout)
        return {**meta, "saved_to": str(dest), "bytes": got}

    # -- live channels (context-managed sync iterators) ------------------
    def logs(self, *, follow: bool = True) -> SyncChannel:
        """Stream logs. ``with sb.logs() as s: for line in s: ...``"""
        return SyncChannel(_ws.ws_url(self._cfg, self.uuid, "logs"), _ws.decode_text)

    def shell(self) -> SyncChannel:
        """An interactive shell stream (send keystrokes with ``.send()``)."""
        return SyncChannel(_ws.ws_url(self._cfg, self.uuid, "shell"), _ws.decode_text)

    def screen(self, *, source: str = "scrcpy") -> SyncChannel:
        """Raw screen frames (binary H.264/PNG). ``source`` is ``host`` or ``scrcpy``."""
        return SyncChannel(_ws.ws_url(self._cfg, self.uuid, "screen/stream", source=source),
                           _ws.decode_bytes)

    def screen_webrtc(self) -> SyncChannel:
        """WebRTC screen signaling (SDP/ICE JSON frames). The browser is the media
        peer; to actually view, open ``webrtc_player_url()`` in the console or the
        standalone player rather than consuming this channel directly."""
        return SyncChannel(_ws.ws_url(self._cfg, self.uuid, "screen/webrtc"), _ws.decode_json)

    def webrtc_player_url(self) -> str:
        """The control-plane WebRTC signaling URL (ws://…/screen/webrtc?token=…)
        to paste into a browser WebRTC player."""
        return _ws.ws_url(self._cfg, self.uuid, "screen/webrtc")

    def adb(self) -> SyncChannel:
        """Raw adb transport bytes (bridge to a local port to ``adb connect``)."""
        return SyncChannel(_ws.ws_url(self._cfg, self.uuid, "adb"), _ws.decode_bytes)

    def vnc(self) -> SyncChannel:
        """Raw RFB (VNC) bytes — iOS VM only."""
        return SyncChannel(_ws.ws_url(self._cfg, self.uuid, "vnc"), _ws.decode_bytes)

    def console(self, *, process: str | None = None) -> SyncChannel:
        """An lldb debugger console stream."""
        return SyncChannel(_ws.ws_url(self._cfg, self.uuid, "debugger/console", process=process),
                           _ws.decode_text)

    def mitm_flows(self) -> SyncChannel:
        """Captured HTTP(S) flow summaries (JSON frames)."""
        return SyncChannel(_ws.ws_url(self._cfg, self.uuid, "mitm/flows"), _ws.decode_json)

    def mitm_ca(self) -> bytes:
        """The mitmproxy CA certificate (PEM bytes)."""
        return self._http.get_content(f"{self._base}/mitm/ca")

    def tunnel(self, to_host: str, to_port: int) -> Tunnel:
        """A reverse tunnel forwarding guest proxy traffic into ``to_host:to_port``."""
        return Tunnel(self._cfg, self.uuid, to_host, to_port)

    # -- local bridges (expose a device channel on a local TCP port) ------
    def adb_bridge(self, host: str = "127.0.0.1", port: int = 0) -> "LocalBridge":
        """A local listener bridged to the device's adb (Android). Start it, then
        ``adb connect <host>:<port>``. ``port`` 0 lets the OS pick one."""
        return LocalBridge(self._cfg, self.uuid, "adb", host, port)

    def vnc_bridge(self, host: str = "127.0.0.1", port: int = 0) -> "LocalBridge":
        """A local listener bridged to the device's VNC/RFB screen (iOS VM).
        Start it, then point a VNC viewer at ``<host>:<port>``."""
        return LocalBridge(self._cfg, self.uuid, "vnc", host, port)

    def screen_bridge(self, host: str = "127.0.0.1", port: int = 0,
                      source: str = "scrcpy") -> "LocalBridge":
        """A local listener bridged to the raw screen stream (Android)."""
        return LocalBridge(self._cfg, self.uuid, "screen/stream", host, port, source=source)

    def gdb_bridge(self, host: str = "127.0.0.1", port: int = 0) -> "LocalBridge":
        """A local listener bridged to a sandbox's guest-kernel gdb stub. Start it,
        then ``gdb-multiarch vmlinux`` and ``target remote <host>:<port>`` (or lldb).
        Cuttlefish debug sandboxes and iOS VMs (capability ``kernel-debug``)."""
        return LocalBridge(self._cfg, self.uuid, "gdb", host, port)


class Files:
    """``sandbox.files`` — list, download and upload files on the device."""

    def __init__(self, http: HttpClient, cfg: Config, uuid: str):
        self._http = http
        self._cfg = cfg
        self._base = f"/sandboxes/{uuid}"

    def list(self, path: str = "") -> dict[str, Any]:
        """List a directory on the device (default: the platform's home)."""
        params = {"path": path} if path else None
        return self._http.get(f"{self._base}/files", params=params)

    def download(self, path: str, dest: str | Path) -> int:
        """Download a device file to ``dest`` via a short-lived signed grant.
        Returns bytes written."""
        grant = self._http.post(f"{self._base}/files/grant", json={"path": path})
        return self._http.download(self._cfg.url.rstrip("/") + grant["url"], Path(dest))

    def upload(self, local: str | Path, path: str | None = None) -> dict[str, Any]:
        """Upload a local file into device directory ``path``."""
        data = {"path": path} if path else None
        return self._http.post_files(f"{self._base}/files/upload",
                                     files=[("file", Path(local))], data=data)


class Apps:
    """``sandbox.apps`` — list, install, uninstall and pull apps."""

    def __init__(self, http: HttpClient, cfg: Config, uuid: str):
        self._http = http
        self._cfg = cfg
        self._base = f"/sandboxes/{uuid}"

    def list(self) -> dict[str, Any]:
        """List installed apps/packages."""
        return self._http.get(f"{self._base}/apps")

    def install(self, *apks: str | Path) -> dict[str, Any]:
        """Install an ``.apk``/``.ipa`` — pass several parts for a split-APK set."""
        if not apks:
            raise ValueError("install() needs at least one file")
        return self._http.post_files(f"{self._base}/apps/install",
                                     files=[("file", Path(a)) for a in apks])

    def uninstall(self, package: str) -> dict[str, Any]:
        """Uninstall a package by id."""
        return self._http.post(f"{self._base}/apps/uninstall", json={"package": package})

    def download(self, package: str, dest: str | Path) -> int:
        """Pull an installed app's APK(s) to ``dest`` via a signed grant."""
        grant = self._http.post(f"{self._base}/apps/grant", json={"package": package})
        return self._http.download(self._cfg.url.rstrip("/") + grant["url"], Path(dest))

    def launch(self, package: str) -> dict[str, Any]:
        """Launch an installed app by package id."""
        return self._http.post(f"{self._base}/control", json={"action": "launch", "app": package})


class Frida:
    """``sandbox.frida`` — the frida-server and script injection on the device.

    All methods go through ``POST /sandboxes/<uuid>/frida`` (capability
    ``frida``). ``inject`` is Android-only today; ``verify`` runs the Stalker
    check on iOS.
    """

    def __init__(self, http: HttpClient, cfg: Config, uuid: str):
        self._http = http
        self._cfg = cfg
        self._uuid = uuid
        self._base = f"/sandboxes/{uuid}/frida"

    def status(self) -> dict[str, Any]:
        """Report frida-server state (``installed``/``running``/``version``/``port``)."""
        return self._http.get(self._base)

    def install(self) -> dict[str, Any]:
        """Install frida-server on the device (slow; pulls packages) and start it."""
        return self._http.post(self._base, json={"action": "install"})

    def start(self) -> dict[str, Any]:
        """Start frida-server."""
        return self._http.post(self._base, json={"action": "start"})

    def stop(self) -> dict[str, Any]:
        """Stop frida-server."""
        return self._http.post(self._base, json={"action": "stop"})

    def verify(self, process: str | None = None) -> dict[str, Any]:
        """Prove frida works by attaching and tracing a process. Returns the
        result plus the script ``messages`` it collected."""
        return self._http.post(self._base, json={"action": "verify", "process": process})

    def inject(self, script: str, process: str, timeout: float = 6.0) -> dict[str, Any]:
        """Run a frida ``script`` against ``process`` for ``timeout`` seconds
        (1-30), then detach. Returns the script's ``send()``/``console`` output
        as ``messages``. Android only."""
        return self._http.post(self._base, json={
            "action": "inject", "script": script, "process": process, "timeout": timeout})

    def run_script(self, path: str | Path, process: str, timeout: float = 6.0) -> dict[str, Any]:
        """Like :meth:`inject`, but read the script from a local file ``path``."""
        return self.inject(Path(path).read_text(), process, timeout)

    def stream(self, script: str, process: str, timeout: float = 0.0) -> SyncChannel:
        """Run a frida ``script`` against ``process`` and stream each message as
        it arrives, instead of collecting them. Returns a context-managed sync
        channel of decoded frida messages (dicts). ``timeout`` <= 0 streams until
        you leave the block (bounded by a server-side cap). Android only.

        >>> with sb.frida.stream(src, "com.example.app") as s:
        ...     for message in s:
        ...         print(message)
        """
        url = _ws.ws_url(self._cfg, self._uuid, "frida/stream",
                         process=process, timeout=timeout)
        return SyncChannel(url, _ws.decode_json, open_send=script)

    def stream_script(self, path: str | Path, process: str, timeout: float = 0.0) -> SyncChannel:
        """Like :meth:`stream`, but read the script from a local file ``path``."""
        return self.stream(Path(path).read_text(), process, timeout)


class Debugger:
    """``sandbox.debugger`` — the on-device lldb (lldb-server + attach).

    Status/install/start go through ``POST /sandboxes/<uuid>/debugger`` (gated
    like the shell); ``console`` opens the interactive lldb stream. Needs a
    rootable image for ptrace, so on Cuttlefish use a debug sandbox.
    """

    def __init__(self, http: HttpClient, cfg: Config, uuid: str):
        self._http = http
        self._cfg = cfg
        self._uuid = uuid
        self._base = f"/sandboxes/{uuid}/debugger"

    def status(self) -> dict[str, Any]:
        """Report lldb-server state (``installed``/``running``/``port``)."""
        return self._http.get(self._base)

    def install(self) -> dict[str, Any]:
        """Push lldb-server to the device (needs root) and start it."""
        return self._http.post(self._base, json={"action": "install"})

    def start(self, process: str | None = None) -> dict[str, Any]:
        """Start lldb-server, optionally attaching it to ``process``."""
        return self._http.post(self._base, json={"action": "start", "process": process})

    def console(self, process: str | None = None) -> SyncChannel:
        """An interactive lldb console stream (send commands with ``.send()``).

        >>> with sb.debugger.console(process="com.example.app") as c:
        ...     c.send("bt")
        ...     for line in c:
        ...         print(line)
        """
        return SyncChannel(_ws.ws_url(self._cfg, self._uuid, "debugger/console", process=process),
                           _ws.decode_text)


class SandboxSnapshots:
    """``sandbox.snapshots`` — point-in-time snapshots of this sandbox."""

    def __init__(self, http: HttpClient, uuid: str):
        self._http = http
        self._base = f"/sandboxes/{uuid}"

    def list(self) -> List[SnapshotRow]:
        """List this sandbox's snapshots."""
        return self._http.get(f"{self._base}/snapshots")

    def create(self, name: str) -> dict[str, Any]:
        """Take a snapshot."""
        return self._http.post(f"{self._base}/snapshots", json={"name": name})

    def restore(self, name: str) -> dict[str, Any]:
        """Restore the sandbox to a snapshot."""
        return self._http.post(f"{self._base}/snapshots/{name}")

    def delete(self, name: str) -> dict[str, Any]:
        """Delete a snapshot."""
        return self._http.delete(f"{self._base}/snapshots/{name}")

    def save_as_template(self, name: str, *, visibility: str = "private",
                         description: str = "", snapshot: str | None = None) -> SnapshotRow:
        """Save the sandbox (or one of its snapshots) as a reusable template."""
        body: dict[str, Any] = {"name": name, "visibility": visibility, "description": description}
        if snapshot is not None:
            body["snapshot"] = snapshot
        return self._http.post(f"{self._base}/template", json=body)
