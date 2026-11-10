# Python SDK reference

```bash
pip install tryorchard-sdk
```

The distribution is `tryorchard-sdk`; the import name is `orchard_sdk`.

Every snippet below assumes:

```python
from orchard_sdk import Orchard

orchard = Orchard.from_env()
sb = orchard.sandbox("my-pixel")
```

REST calls return the server's JSON as plain `dict`/`list` (typed as `TypedDict`s for editors). Live channels are context-managed iterators.

## Contents

- [Client](#client)
- [Config](#config)
- [Sandboxes](#sandboxes)
- [Sandbox](#sandbox)
  - [Lifecycle](#lifecycle)
  - [Input](#input)
  - [Inspection](#inspection)
  - [Live channels](#live-channels)
  - [Local bridges and tunnel](#local-bridges-and-tunnel)
- [Files](#files)
- [Apps](#apps)
- [Frida](#frida)
- [Debugger](#debugger)
- [Sandbox snapshots](#sandbox-snapshots)
- [Snapshots](#snapshots)
- [Templates](#templates)
- [Catalog](#catalog)
- [Jobs](#jobs)
- [Nodes](#nodes)
- [Keys](#keys)
- [Team](#team)
- [Workspaces](#workspaces)
- [Remote](#remote)
- [Channels](#channels)
- [Async channels](#async-channels)
- [Selectors](#selectors)
- [Errors](#errors)

## Client

### `Orchard(url=None, token=None, org=None, ws=None, *, timeout=60.0)`

Create a client; explicit arguments win over `ORCHARD_*` environment variables.

```python
orchard = Orchard("https://orchard.example.com", "orc_live_xxx")
```

```python
orchard = Orchard("https://orchard.example.com", jwt, org="acme", ws="mobile", timeout=120)
```

### `Orchard.from_env(*, timeout=60.0)`

Build a client from `ORCHARD_API_URL`, `ORCHARD_API_KEY`, and optional `ORCHARD_ORG` / `ORCHARD_WS`.

```python
orchard = Orchard.from_env()
```

```python
orchard = Orchard.from_env(timeout=300)  # long installs
```

### `orchard.me()`

The authenticated identity: orgs, active org/workspace, features.

```python
me = orchard.me()
print(me["username"], me["active"]["name"])
```

### `orchard.sandbox(selector)`

Resolve a uuid, uuid prefix, name or tag to one `Sandbox`; raises `SelectorError` on zero or several matches.

```python
sb = orchard.sandbox("a31eba21")
```

```python
sb = orchard.sandbox("payments")  # by tag, must be unique
```

### `orchard.close()` / context manager

Close the HTTP connection pool.

```python
with Orchard.from_env() as orchard:
    print(len(orchard.sandboxes.list()["instances"]))
```

```python
orchard = Orchard.from_env()
try:
    orchard.sandbox("my-pixel").start()
finally:
    orchard.close()
```

### `orchard.config`

The resolved `Config`.

```python
print(orchard.config.url, orchard.config.org)
```

## Config

### `from_env(url=None, token=None, org=None, ws=None, timeout=60.0)`

Resolve a `Config` from arguments and environment; raises `ValueError` if URL or token is missing.

```python
from orchard_sdk import from_env

cfg = from_env()
```

```python
cfg = from_env("https://orchard.example.com", "orc_live_xxx", ws="mobile")
```

### `Config(url, token, org=None, ws=None, timeout=60.0)`

Dataclass of connection settings, with `api_base` and `ws_base` properties.

```python
from orchard_sdk import Config

cfg = Config(url="https://orchard.example.com", token="orc_live_xxx")
print(cfg.api_base)  # https://orchard.example.com/api
print(cfg.ws_base)   # wss://orchard.example.com
```

| Variable | Meaning |
| --- | --- |
| `ORCHARD_API_URL` | Control-plane URL (`ORCHARD_URL` also accepted) |
| `ORCHARD_API_KEY` | API key (`orc_…`) or JWT access token |
| `ORCHARD_ORG` | Org slug (ignored for API keys) |
| `ORCHARD_WS` | Workspace slug |

## Sandboxes

### `orchard.sandboxes.list()`

Every sandbox visible to this key/org, as `{"instances": [...], "errors": [...]}`.

```python
for s in orchard.sandboxes.list()["instances"]:
    print(s["name"], s["state"], s.get("tag"))
```

```python
running = [s for s in orchard.sandboxes.list()["instances"] if s["state"] == "running"]
```

### `orchard.sandboxes.create(**spec)`

Create a sandbox from `platform`, `name`, `cpu`, `memory_mb` and platform fields (`image`/`device` for Android, `preset`/`variant` for iOS).

```python
inst = orchard.sandboxes.create(platform="android", name="ci-pixel",
                                image="android-34", device="pixel_7", cpu=4, memory_mb=4096)
```

```python
inst = orchard.sandboxes.create(platform="ios", name="ios-17", preset="jailbreak", variant="iphone")
```

### `orchard.sandboxes.create_sim(**spec)`

Create an iOS simulator sandbox from `name`, `device_type`, `runtime`.

```python
orchard.sandboxes.create_sim(name="sim-15",
                             device_type="com.apple.CoreSimulator.SimDeviceType.iPhone-15",
                             runtime="com.apple.CoreSimulator.SimRuntime.iOS-17-5")
```

### `orchard.sandboxes.resolve(selector)`

Resolve a selector to one instance dict.

```python
inst = orchard.sandboxes.resolve("my-pixel")
print(inst["uuid"], inst["node"])
```

### `orchard.sandboxes.resolve_all(selector)`

Every instance a selector matches; tags can match many.

```python
for inst in orchard.sandboxes.resolve_all("payments"):
    orchard.sandboxes.get(inst["uuid"]).stop()
```

### `orchard.sandboxes.get(uuid)`

A `Sandbox` handle for a known uuid, with no lookup.

```python
sb = orchard.sandboxes.get("a31eba21-953b-4184-8ed7-5cf3bd062615")
```

## Sandbox

`sb.uuid` holds the sandbox uuid. Sub-namespaces: `sb.files`, `sb.apps`, `sb.frida`, `sb.debugger`, `sb.snapshots`.

### Lifecycle

### `sb.get()`

Fetch the current instance dict.

```python
inst = sb.get()
print(inst["state"], inst["hardware"]["cpu"])
```

```python
caps = {k: c["available"] for k, c in sb.get()["capabilities"].items()}
```

### `sb.start()`

Boot the sandbox.

```python
sb.start()
```

### `sb.stop()`

Stop the sandbox.

```python
sb.stop()
```

### `sb.delete()`

Terminate the sandbox and delete its disk on the node.

```python
sb.delete()
```

### `sb.edit(*, notes=None, tag=None, tag_color=None, owner=None, cpu=None, memory_mb=None)`

Change metadata or size; `cpu`/`memory_mb` require the sandbox stopped, `owner` requires org admin. Raises `ValueError` with no fields.

```python
sb.edit(notes="login regression repro")
```

```python
sb.stop()
sb.edit(cpu=6, memory_mb=8192)
```

### `sb.tag(tag, color=None)`

Set the tag and optional `#rrggbb` chip color.

```python
sb.tag("payments", "#22c55e")
```

### Input

### `sb.control(action, **kw)`

Send a raw unified input action (`tap`, `swipe`, `key`, `text`, `launch`, `tap_text`, `launch_intent`).

```python
sb.control("tap", x=540, y=1200)
```

```python
sb.control("key", name="back")
```

### `sb.tap(x, y)`

Tap at device pixel coordinates.

```python
sb.tap(540, 1200)
```

### `sb.swipe(x1, y1, x2, y2, ms=300)`

Swipe from one point to another over `ms` milliseconds.

```python
sb.swipe(540, 1800, 540, 400)          # scroll down
```

```python
sb.swipe(100, 1000, 900, 1000, ms=800) # slow horizontal drag
```

### `sb.key(name)`

Press a hardware or navigation key (`home`, `back`, `enter`, `power`, …).

```python
sb.key("home")
```

```python
sb.key("enter")
```

### `sb.text(text)` / `sb.type_text(text)`

Type into the focused field; `type_text` is an alias.

```python
sb.tap_text("Email")
sb.text("qa@example.com")
```

```python
sb.type_text("hunter2")
```

### `sb.tap_text(text)`

Find an on-screen element whose label matches `text` and tap it.

```python
sb.tap_text("Sign in")
```

### `sb.launch(app)`

Launch an app by package id (Android) or bundle id (iOS).

```python
sb.launch("com.android.settings")
```

```python
sb.launch("com.apple.Preferences")
```

### `sb.launch_intent(package, component, *, action=None, data=None, extras=None)`

Start an exported Android activity with an optional intent action, data URI and string extras.

```python
sb.launch_intent("com.example.app", ".MainActivity")
```

```python
sb.launch_intent("com.example.app", "com.example.app.DeepLinkActivity",
                 action="android.intent.action.VIEW",
                 data="example://orders/42", extras={"source": "qa"})
```

### Inspection

### `sb.screenshot()`

A PNG/JPEG screenshot as raw bytes.

```python
from pathlib import Path

Path("screen.png").write_bytes(sb.screenshot())
```

### `sb.describe_ui()`

The accessibility/UI tree.

```python
tree = sb.describe_ui()
```

### `sb.metrics()`

Live CPU, memory, battery and uptime.

```python
m = sb.metrics()
print(m)
```

### `sb.storage()`

Disk usage breakdown (apps, media, system, free).

```python
print(sb.storage())
```

### Live channels

Each returns a [`SyncChannel`](#channels): open it with `with`, iterate, optionally `send()`.

### `sb.logs(*, follow=True)`

Stream log lines.

```python
with sb.logs() as stream:
    for line in stream:
        print(line)
```

```python
import itertools

with sb.logs() as stream:
    first_100 = list(itertools.islice(stream, 100))
```

### `sb.shell()`

Interactive shell stream; send keystrokes with `send()`.

```python
with sb.shell() as sh:
    sh.send("getprop ro.build.version.release\n")
    for out in sh:
        print(out, end="")
```

### `sb.screen(*, source="scrcpy")`

Raw binary screen frames; `source` is `"host"` or `"scrcpy"`.

```python
with sb.screen() as frames, open("screen.h264", "wb") as f:
    for chunk in frames:
        f.write(chunk)
```

```python
with sb.screen(source="host") as frames:
    first = next(iter(frames))
```

### `sb.screen_webrtc()`

WebRTC signaling channel (SDP/ICE JSON frames); for viewing, use `webrtc_player_url()` in a browser.

```python
with sb.screen_webrtc() as sig:
    for msg in sig:
        print(msg.get("type"))
```

### `sb.webrtc_player_url()`

The WebRTC signaling URL (with token) to paste into a browser WebRTC player.

```python
print(sb.webrtc_player_url())
```

### `sb.adb()`

Raw adb transport bytes; usually consumed via `adb_bridge()`.

```python
with sb.adb() as raw:
    for chunk in raw:
        handle(chunk)
```

### `sb.vnc()`

Raw RFB (VNC) bytes. iOS VM only.

```python
with sb.vnc() as rfb:
    print(next(iter(rfb))[:12])  # b"RFB 003.008\n"
```

### `sb.console(*, process=None)`

An lldb debugger console stream.

```python
with sb.console(process="com.example.app") as c:
    c.send("bt\n")
    for line in c:
        print(line)
```

### `sb.mitm_flows()`

Captured HTTP(S) flow summaries as decoded JSON (`method`, `scheme`, `host`, `path`, `status`, `content_type`, …). Capture must be started for the sandbox in the console.

```python
with sb.mitm_flows() as flows:
    for flow in flows:
        print(flow["method"], flow["status"], flow["host"] + flow["path"])
```

### `sb.mitm_ca()`

The mitmproxy CA certificate as PEM bytes. Raises `ApiError` (404) until capture has run once.

```python
open("orchard-mitm.pem", "wb").write(sb.mitm_ca())
```

### Local bridges and tunnel

### `sb.tunnel(to_host, to_port)`

A reverse tunnel forwarding guest proxy traffic to a local proxy (Burp, mitmproxy); see [`Tunnel.run`](#tunnelrunon_eventnone).

```python
sb.tunnel("127.0.0.1", 8080).run(lambda level, text: print(level, text))
```

### `sb.adb_bridge(host="127.0.0.1", port=0)`

A local TCP listener bridged to the device's adb (Android); `port=0` lets the OS pick.

```python
import subprocess

with sb.adb_bridge() as b:
    subprocess.run(["adb", "connect", f"127.0.0.1:{b.port}"], check=True)
    subprocess.run(["adb", "-s", f"127.0.0.1:{b.port}", "shell", "id"])
```

```python
b = sb.adb_bridge(port=5555).start()
input("adb connect 127.0.0.1:5555, then press Enter to stop")
b.close()
```

### `sb.vnc_bridge(host="127.0.0.1", port=0)`

A local listener bridged to the VNC/RFB screen (iOS VM).

```python
with sb.vnc_bridge(port=5900) as b:
    input(f"point a VNC viewer at 127.0.0.1:{b.port}, Enter to stop")
```

### `sb.screen_bridge(host="127.0.0.1", port=0, source="scrcpy")`

A local listener bridged to the raw screen stream (Android).

```python
with sb.screen_bridge() as b:
    print("raw frames on port", b.port)
    input()
```

### `sb.gdb_bridge(host="127.0.0.1", port=0)`

A local listener bridged to the guest-kernel gdb stub. Cuttlefish debug sandboxes only (capability `kernel-debug`).

```python
with sb.gdb_bridge(port=1234) as b:
    input(f"gdb vmlinux -ex 'target remote 127.0.0.1:{b.port}'  (Enter to stop)")
```

## Files

### `sb.files.list(path="")`

List a device directory (default: the platform's home).

```python
print(sb.files.list())
```

```python
print(sb.files.list("/sdcard/Download"))
```

### `sb.files.download(path, dest)`

Download a device file to `dest` via a short-lived signed grant; returns bytes written.

```python
n = sb.files.download("/sdcard/Download/report.pdf", "report.pdf")
print(n, "bytes")
```

### `sb.files.upload(local, path=None)`

Upload a local file into device directory `path`.

```python
sb.files.upload("./fixtures/photo.jpg", "/sdcard/Pictures")
```

```python
sb.files.upload("./build/app.apk", "/data/local/tmp")
```

## Apps

### `sb.apps.list()`

List installed apps/packages.

```python
print(sb.apps.list())
```

### `sb.apps.install(*apks)`

Install an `.apk`/`.ipa`, or several parts of a split-APK set. Raises `ValueError` with no files.

```python
sb.apps.install("./build/app-release.apk")
```

```python
sb.apps.install("base.apk", "split_config.arm64_v8a.apk", "split_config.en.apk")
```

### `sb.apps.uninstall(package)`

Uninstall a package by id.

```python
sb.apps.uninstall("com.example.app")
```

### `sb.apps.download(package, dest)`

Pull an installed app's APK(s) to `dest` via a signed grant; returns bytes written.

```python
sb.apps.download("com.example.app", "pulled.apk")
```

### `sb.apps.launch(package)`

Launch an installed app by package id.

```python
sb.apps.launch("com.example.app")
```

## Frida

Requires capability `frida`.

### `sb.frida.status()`

frida-server state (`installed`, `running`, `version`, `port`).

```python
st = sb.frida.status()
if not st.get("running"):
    sb.frida.start()
```

### `sb.frida.install()`

Install frida-server (slow) and start it.

```python
sb.frida.install()
```

### `sb.frida.start()`

Start frida-server.

```python
sb.frida.start()
```

### `sb.frida.stop()`

Stop frida-server.

```python
sb.frida.stop()
```

### `sb.frida.verify(process=None)`

Attach and trace a process to prove frida works; returns the result and collected `messages`. Runs the Stalker check on iOS.

```python
print(sb.frida.verify())
```

```python
print(sb.frida.verify("com.example.app")["messages"])
```

### `sb.frida.inject(script, process, timeout=6.0)`

Run a script against a process for `timeout` seconds (1–30), then detach; returns `send()`/console output as `messages`. Android only.

```python
src = 'send(Process.enumerateModules().length)'
print(sb.frida.inject(src, "com.example.app")["messages"])
```

```python
src = """
Java.perform(() => {
  const Activity = Java.use("android.app.Activity");
  Activity.onResume.implementation = function () {
    send("onResume " + this.getClass().getName());
    return this.onResume();
  };
});
"""
res = sb.frida.inject(src, "com.example.app", timeout=15)
```

### `sb.frida.run_script(path, process, timeout=6.0)`

Like `inject`, reading the script from a local file.

```python
res = sb.frida.run_script("hooks/ssl_pinning.js", "com.example.app", timeout=10)
```

### `sb.frida.stream(script, process, timeout=0.0)`

Run a script and stream each message as it arrives; `timeout <= 0` streams until you leave the block (server-capped). Android only.

```python
with sb.frida.stream(src, "com.example.app") as s:
    for message in s:
        print(message)
```

```python
import itertools

with sb.frida.stream(src, "com.example.app", timeout=20) as s:
    first_10 = list(itertools.islice(s, 10))
```

### `sb.frida.stream_script(path, process, timeout=0.0)`

Like `stream`, reading the script from a local file.

```python
with sb.frida.stream_script("hooks/trace_crypto.js", "com.example.app") as s:
    for message in s:
        print(message)
```

## Debugger

On-device lldb. Needs a rootable image for ptrace (on Cuttlefish, a debug sandbox).

### `sb.debugger.status()`

lldb-server state (`installed`, `running`, `port`).

```python
print(sb.debugger.status())
```

### `sb.debugger.install()`

Push lldb-server to the device (needs root) and start it.

```python
sb.debugger.install()
```

### `sb.debugger.start(process=None)`

Start lldb-server, optionally attached to `process`.

```python
sb.debugger.start()
```

```python
sb.debugger.start("com.example.app")
```

### `sb.debugger.console(process=None)`

Interactive lldb console stream; send commands with `send()`.

```python
with sb.debugger.console(process="com.example.app") as c:
    c.send("bt\n")
    for line in c:
        print(line)
```

## Sandbox snapshots

### `sb.snapshots.list()`

This sandbox's snapshots.

```python
for snap in sb.snapshots.list():
    print(snap["name"], snap["created_at"])
```

### `sb.snapshots.create(name)`

Take a snapshot.

```python
sb.snapshots.create("clean-install")
```

### `sb.snapshots.restore(name)`

Restore the sandbox to a snapshot.

```python
sb.snapshots.restore("clean-install")
```

### `sb.snapshots.delete(name)`

Delete a snapshot.

```python
sb.snapshots.delete("clean-install")
```

### `sb.snapshots.save_as_template(name, *, visibility="private", description="", snapshot=None)`

Save the sandbox, or one of its snapshots, as a reusable template.

```python
tpl = sb.snapshots.save_as_template("pixel-with-app")
```

```python
tpl = sb.snapshots.save_as_template("pixel-logged-in", visibility="org",
                                    description="test user signed in", snapshot="logged-in")
```

## Snapshots

### `orchard.snapshots.list()`

Every point snapshot in the org/workspace.

```python
for snap in orchard.snapshots.list():
    print(snap["instance_uuid"], snap["name"])
```

## Templates

### `orchard.templates.list()`

Available templates.

```python
for t in orchard.templates.list():
    print(t["id"], t["name"], t["visibility"])
```

### `orchard.templates.launch(pk, name, **spec)`

Launch a new sandbox from a template.

```python
orchard.templates.launch(12, "ci-run-481")
```

```python
orchard.templates.launch(12, "ci-run-482", cpu=4, memory_mb=4096)
```

### `orchard.templates.delete(pk)`

Delete a template.

```python
orchard.templates.delete(12)
```

## Catalog

### `orchard.catalog.android()`

Android system images and device profiles.

```python
print(orchard.catalog.android())
```

### `orchard.catalog.presets()`

iOS patch presets.

```python
print(orchard.catalog.presets())
```

### `orchard.catalog.sim_device_types()`

iOS simulator device types and runtimes.

```python
print(orchard.catalog.sim_device_types())
```

### `orchard.catalog.providers()`

Per-node provider availability (platform admin only).

```python
for row in orchard.catalog.providers():
    print(row)
```

## Jobs

### `orchard.jobs.list()`

Background jobs (image downloads, VM creates).

```python
for j in orchard.jobs.list():
    print(j["node"], j["id"], j["state"], j.get("progress"))
```

### `orchard.jobs.cancel(node, job_id)`

Cancel a running job.

```python
orchard.jobs.cancel("node-1", "c0ffee12")
```

### `orchard.jobs.logs(node, kind, name)`

Stream a job's log lines.

```python
with orchard.jobs.logs("node-1", "image", "android-34") as s:
    for line in s:
        print(line)
```

## Nodes

Mostly platform admin.

### `orchard.nodes.list()`

Placeable nodes.

```python
for n in orchard.nodes.list():
    print(n)
```

### `orchard.nodes.test(**cfg)`

Probe an agent URL and token before enrolling.

```python
orchard.nodes.test(agent_url="https://node-2.internal:8443", agent_token="nt_xxx")
```

### `orchard.nodes.create(**cfg)`

Enroll a node (`name`, `agent_url`, `agent_token`).

```python
orchard.nodes.create(name="node-2", agent_url="https://node-2.internal:8443", agent_token="nt_xxx")
```

### `orchard.nodes.refresh(pk)`

Re-poll one node.

```python
orchard.nodes.refresh(2)
```

### `orchard.nodes.delete(pk)`

Remove a node.

```python
orchard.nodes.delete(2)
```

## Keys

### `orchard.keys.list()`

The caller's API keys (metadata only; secrets are never returned).

```python
for k in orchard.keys.list():
    print(k["id"], k["name"], k["hint"], k.get("expires_at"))
```

### `orchard.keys.create(name, *, sandbox_uuids=None, tag=None, allowed_features=None, expires_in_days=None)`

Mint a key; the secret is in `token` and shown once. Omit all scopes for a full org-wide key.

```python
key = orchard.keys.create("ci", sandbox_uuids=[sb.uuid],
                          allowed_features=["logs", "files"], expires_in_days=30)
print(key["token"])
```

```python
key = orchard.keys.create("payments-team", tag="payments")  # every sandbox tagged payments
```

### `orchard.keys.delete(key_id)`

Revoke a key.

```python
orchard.keys.delete(key["id"])
```

## Team

The active organization.

### `orchard.team.get()`

The org, its usage, features and member count.

```python
print(orchard.team.get())
```

### `orchard.team.edit(**fields)`

Change org fields (org admin only).

```python
orchard.team.edit(name="Acme Mobile QA")
```

### `orchard.team.invite_info(token)`

Describe an invite token.

```python
print(orchard.team.invite_info("inv_xxx"))
```

### `orchard.team.accept_invite(token, **account)`

Accept an invite, optionally creating an account with `username`/`password`/`email`.

```python
orchard.team.accept_invite("inv_xxx")
```

```python
orchard.team.accept_invite("inv_xxx", username="sam", password="…", email="sam@example.com")
```

### `orchard.team.members.list()`

Org members.

```python
for m in orchard.team.members.list():
    print(m)
```

### `orchard.team.members.edit(pk, **fields)`

Change a member's `role`, `denied_features` or limits.

```python
orchard.team.members.edit(7, role="admin")
```

```python
orchard.team.members.edit(7, denied_features=["shell", "frida"])
```

### `orchard.team.members.remove(pk)`

Remove a member.

```python
orchard.team.members.remove(7)
```

### `orchard.team.invites.list()`

Pending invites.

```python
print(orchard.team.invites.list())
```

### `orchard.team.invites.create(role="member")`

Create an invite; `token` in the response is the one-time join credential.

```python
inv = orchard.team.invites.create()
print(inv["token"])
```

```python
inv = orchard.team.invites.create(role="admin")
```

### `orchard.team.invites.delete(pk)`

Revoke an invite.

```python
orchard.team.invites.delete(3)
```

## Workspaces

### `orchard.workspaces.list()`

The caller's workspaces (from `/api/me`).

```python
for w in orchard.workspaces.list():
    print(w["slug"], w["name"])
```

### `orchard.workspaces.create(name, slug=None)`

Create a workspace (org admin).

```python
orchard.workspaces.create("Payments")
```

```python
orchard.workspaces.create("Payments QA", slug="payments-qa")
```

### `orchard.workspaces.get(slug)`

A handle to one workspace, with `slug`, `members` and `invites` (same methods as [Team](#team)).

```python
ws = orchard.workspaces.get("payments-qa")
print(ws.members.list())
inv = ws.invites.create(role="member")
```

### `workspace.edit(**fields)`

Change workspace fields.

```python
orchard.workspaces.get("payments-qa").edit(name="Payments")
```

### `workspace.delete()`

Delete the workspace (must be empty; the default cannot be deleted).

```python
orchard.workspaces.get("payments-qa").delete()
```

## Remote

Cloud sandboxes (e2b, daytona, modal). `ref` is the remote sandbox's uuid or legacy numeric record id.

### `orchard.remote.catalog()`

Which cloud providers are available and configured.

```python
print(orchard.remote.catalog())
```

### `orchard.remote.credentials()`

Stored provider credentials.

```python
for c in orchard.remote.credentials():
    print(c)
```

### `orchard.remote.add_credential(provider, key, label=None, config=None)`

Store and verify a provider API key.

```python
orchard.remote.add_credential("e2b", "e2b_xxx")
```

```python
orchard.remote.add_credential("daytona", "dtn_xxx", label="eu", config={"region": "eu"})
```

### `orchard.remote.delete_credential(ref)`

Delete a stored credential.

```python
orchard.remote.delete_credential(4)
```

### `orchard.remote.create(provider, name, **spec)`

Create a remote sandbox (`image`, `cpu`, `memory_mb`, `region`, `ttl_minutes`, …).

```python
r = orchard.remote.create("e2b", "scratch")
```

```python
r = orchard.remote.create("daytona", "build-box", cpu=4, memory_mb=8192, ttl_minutes=60)
```

### `orchard.remote.get(ref)`

Fetch a remote sandbox.

```python
print(orchard.remote.get(r["uuid"]))
```

### `orchard.remote.start(ref)` / `orchard.remote.stop(ref)`

Start or stop a remote sandbox.

```python
orchard.remote.stop(r["uuid"])
orchard.remote.start(r["uuid"])
```

### `orchard.remote.delete(ref)`

Terminate a remote sandbox.

```python
orchard.remote.delete(r["uuid"])
```

### `orchard.remote.upload(ref, local, path=None)`

Upload a local file.

```python
orchard.remote.upload(r["uuid"], "./script.sh", "/home/user")
```

### `orchard.remote.download(ref, path, local=None)`

Download a file to `local` (default: its basename in the cwd); returns bytes written.

```python
orchard.remote.download(r["uuid"], "/home/user/out.log")
```

```python
orchard.remote.download(r["uuid"], "/home/user/out.log", "artifacts/out.log")
```

### `orchard.remote.shell(ref)`

Interactive shell stream.

```python
with orchard.remote.shell(r["uuid"]) as sh:
    sh.send("uname -a\n")
    for out in sh:
        print(out, end="")
```

### `orchard.remote.logs(ref)`

Stream logs.

```python
with orchard.remote.logs(r["uuid"]) as s:
    for line in s:
        print(line)
```

### `orchard.remote.metrics(ref)`

Live CPU, memory and uptime sampled inside the sandbox.

```python
print(orchard.remote.metrics(r["uuid"]))
```

## Channels

### `SyncChannel`

Returned by every streaming method. The socket opens on `with` and closes on exit, including `break` and Ctrl-C. Iteration yields decoded frames (`str`, `bytes` or `dict`) and raises `ChannelClosedError` on an Orchard error close.

```python
with sb.logs() as stream:
    for line in stream:
        if "FATAL" in line:
            break
```

```python
with sb.shell() as sh:
    sh.send("ls /sdcard\n")
    print(next(iter(sh)))
```

- `send(data)` — push a `str` or `bytes` frame upstream. Raises `RuntimeError` if not open.
- `close()` — stop the stream and join the worker thread.

### `LocalBridge`

Returned by the `*_bridge()` methods. `start()` binds and returns self; `port` is the bound port; `close()` stops it. Also a context manager.

```python
from orchard_sdk import LocalBridge

b: LocalBridge = sb.adb_bridge().start()
print(b.host, b.port)
b.close()
```

### `Tunnel.run(on_event=None)`

Block until the server closes the tunnel; `on_event(level, text)` gets `ready`/`warn`/`error`/`close`. Returns `0` on clean close, `1` on refusal.

```python
code = sb.tunnel("127.0.0.1", 8080).run()
```

```python
def log(level: str, text: str) -> None:
    print(f"[{level}] {text}")

sb.tunnel("127.0.0.1", 8080).run(log)
```

## Async channels

REST stays synchronous; for asyncio code use `AsyncChannels(cfg, uuid)`.

```python
import asyncio
from orchard_sdk import from_env
from orchard_sdk.aio import AsyncChannels

ch = AsyncChannels(from_env(), sb.uuid)
```

### `ch.logs()`

Async-iterate log lines.

```python
async def main():
    async for line in ch.logs():
        print(line)

asyncio.run(main())
```

### `ch.shell()`

Async-iterate shell output (read-only).

```python
async for out in ch.shell():
    print(out, end="")
```

### `ch.screen(source="scrcpy")`

Async-iterate raw screen frames.

```python
async for frame in ch.screen(source="host"):
    sink.write(frame)
```

### `ch.adb()`

Async-iterate raw adb bytes.

```python
async for chunk in ch.adb():
    handle(chunk)
```

### `ch.vnc()`

Async-iterate raw RFB bytes (iOS VM).

```python
async for chunk in ch.vnc():
    handle(chunk)
```

### `ch.mitm_flows()`

Async-iterate captured flow summaries.

```python
async for flow in ch.mitm_flows():
    print(flow)
```

Several streams at once:

```python
async def tail(name, it):
    async for item in it:
        print(name, item)

async def main():
    await asyncio.gather(tail("log", ch.logs()), tail("flow", ch.mitm_flows()))
```

## Selectors

`orchard.sandbox()`, `sandboxes.resolve()` and `sandboxes.resolve_all()` try these tiers in order and stop at the first that matches:

1. exact uuid
2. uuid prefix
3. exact `name` or `display_name`
4. tag

Only node sandboxes (with a `uuid`) are candidates. The functions are also importable for your own lists:

```python
from orchard_sdk.selector import resolve, resolve_all

insts = orchard.sandboxes.list()["instances"]
one = resolve(insts, "a31e")
tagged = resolve_all(insts, "payments")
```

## Errors

All inherit `OrchardError`.

| Exception | Raised when | Attributes |
| --- | --- | --- |
| `ApiError` | non-2xx REST response | `status`, `detail`, `user_message` |
| `SelectorError` | selector matched zero or several sandboxes | — |
| `ChannelClosedError` | channel closed with an Orchard code | `code`, `reason` |

| Close code | Meaning |
| --- | --- |
| 4401 | unauthenticated |
| 4403 | forbidden (key scope or capability) |
| 4404 | sandbox not found |
| 4502 | upstream node agent unreachable |

```python
from orchard_sdk import ApiError, ChannelClosedError, OrchardError, SelectorError

try:
    orchard.sandbox("pixel").start()
except SelectorError as e:
    print(e)                      # lists the ambiguous matches
except ApiError as e:
    print(e.status, e.detail)
```

```python
try:
    with sb.shell() as sh:
        for out in sh:
            print(out, end="")
except ChannelClosedError as e:
    if e.code == 4403:
        print("this key lacks the shell capability")
except OrchardError as e:
    print("orchard:", e)
```

`ValueError` is raised for missing config and for `edit()` / `apps.install()` called with nothing to do.
