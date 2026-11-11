# @tryorchard/sdk — API reference

```bash
npm i @tryorchard/sdk
```

Node ≥ 18 or any modern browser. On Node < 21 (no global `WebSocket`) also install the optional peer `ws` (`npm i ws`) to use live channels.

Every example below assumes:

```ts
import { Orchard } from "@tryorchard/sdk";

const orchard = Orchard.fromEnv();
const sb = await orchard.sandbox("my-pixel");
```

## Contents

- [Orchard](#orchard)
- [orchard.sandboxes](#orchardsandboxes)
- [Sandbox](#sandbox) — [lifecycle](#lifecycle), [input](#input), [inspection](#inspection), [live channels](#live-channels)
- [sb.files](#sbfiles)
- [sb.apps](#sbapps)
- [sb.frida](#sbfrida)
- [sb.debugger](#sbdebugger)
- [sb.snapshots](#sbsnapshots)
- [orchard.snapshots](#orchardsnapshots)
- [orchard.templates](#orchardtemplates)
- [orchard.catalog](#orchardcatalog)
- [orchard.jobs](#orchardjobs)
- [orchard.nodes](#orchardnodes)
- [orchard.keys](#orchardkeys)
- [orchard.team](#orchardteam)
- [orchard.workspaces](#orchardworkspaces)
- [orchard.remote](#orchardremote)
- [Channel](#channel)
- [Selectors](#selectors)
- [Errors](#errors)
- [Types](#types)

## Orchard

### `new Orchard(opts?: OrchardOptions)`

Create a client. Options win over the `ORCHARD_API_URL` / `ORCHARD_API_KEY` / `ORCHARD_ORG` / `ORCHARD_WS` environment variables.

| Option | Type | Description |
| --- | --- | --- |
| `url` | `string` | Control-plane base URL. |
| `token` | `string` | API key (`orc_…`) or JWT access token. |
| `org` | `string` | Organization slug (`X-Orchard-Org`). Ignored for API keys. |
| `ws` | `string` | Workspace slug (`X-Orchard-Workspace`). |
| `timeout` | `number` | REST timeout in ms (default `60000`). |

```ts
const orchard = new Orchard({ url: "https://orchard.example.com", token: "orc_live_xxx" });
```

```ts
const orchard = new Orchard({ url: "https://orchard.example.com", token: jwt, org: "acme", ws: "qa", timeout: 120_000 });
```

### `Orchard.fromEnv(): Orchard`

Build a client from the `ORCHARD_*` environment variables (Node).

```ts
const orchard = Orchard.fromEnv();
```

### `orchard.config: ResolvedConfig`

The resolved `{ url, token, org?, ws?, timeout }`.

```ts
console.log(orchard.config.url, orchard.config.timeout);
```

### `orchard.me(): Promise<Record<string, unknown>>`

The authenticated identity: orgs, active org/workspace, features.

```ts
const me = await orchard.me();
console.log(me.username, me.active);
```

### `orchard.sandbox(selector: string): Promise<Sandbox>`

Resolve a uuid, uuid prefix, name or tag to a single `Sandbox`. Throws `SelectorError` on zero or ambiguous matches.

```ts
const sb = await orchard.sandbox("a31eba21");
```

```ts
const sb = await orchard.sandbox("payments");
```

## orchard.sandboxes

### `sandboxes.list(): Promise<InstanceList>`

Every sandbox visible to this key/org.

```ts
const { instances, errors } = await orchard.sandboxes.list();
for (const s of instances) console.log(s.name, s.state, s.tag);
```

```ts
const running = (await orchard.sandboxes.list()).instances.filter((s) => s.state === "running");
```

### `sandboxes.create(spec: Record<string, unknown>): Promise<Instance>`

Create a sandbox (`platform`, `name`, `cpu`, `memory_mb` plus platform fields).

```ts
const inst = await orchard.sandboxes.create({ platform: "android", name: "ci-pixel", cpu: 4, memory_mb: 4096, image: "android-34" });
```

```ts
const inst = await orchard.sandboxes.create({ platform: "ios", name: "ios-17", preset: "default" });
```

### `sandboxes.createSim(spec: Record<string, unknown>): Promise<Instance>`

Create an iOS simulator sandbox (`name`, `device_type`, `runtime`).

```ts
const sim = await orchard.sandboxes.createSim({ name: "sim-15", device_type: "iPhone 15", runtime: "iOS-17-5" });
```

### `sandboxes.resolve(selector: string): Promise<Instance>`

Resolve a selector to one instance row (no handle).

```ts
const inst = await orchard.sandboxes.resolve("my-pixel");
console.log(inst.uuid, inst.node);
```

### `sandboxes.resolveAll(selector: string): Promise<Instance[]>`

Every instance a selector matches (tags match many).

```ts
for (const inst of await orchard.sandboxes.resolveAll("payments")) {
  await orchard.sandboxes.get(inst.uuid!).stop();
}
```

### `sandboxes.get(uuid: string): Sandbox`

A handle for a known uuid, without a lookup.

```ts
const sb = orchard.sandboxes.get("a31eba21-953b-4184-8ed7-5cf3bd062615");
```

## Sandbox

### `sb.uuid: string`

The sandbox uuid.

```ts
console.log(sb.uuid);
```

### Lifecycle

#### `sb.get(): Promise<Instance>`

Fetch the current instance.

```ts
const inst = await sb.get();
console.log(inst.state, inst.runtime.uptime_s);
```

#### `sb.start(): Promise<unknown>`

Boot the sandbox.

```ts
await sb.start();
```

#### `sb.stop(): Promise<unknown>`

Stop the sandbox.

```ts
await sb.stop();
```

#### `sb.delete(): Promise<unknown>`

Terminate the sandbox and delete its disk.

```ts
await sb.delete();
```

#### `sb.edit(patch): Promise<Instance>`

Change `notes`, `tag`, `tag_color`, `owner`, `cpu` or `memory_mb`. `cpu`/`memory_mb` require the sandbox stopped; `owner` requires org admin.

```ts
await sb.edit({ notes: "flaky camera tests" });
```

```ts
await sb.stop();
await sb.edit({ cpu: 6, memory_mb: 8192 });
```

#### `sb.tag(tag: string, color?: string): Promise<Instance>`

Set the tag and optional `#rrggbb` chip colour.

```ts
await sb.tag("payments", "#22c55e");
```

```ts
await sb.tag("");
```

### Input

#### `sb.control(action: string, extra?: Record<string, unknown>): Promise<unknown>`

Send a raw unified input action; the helpers below wrap it.

```ts
await sb.control("tap", { x: 540, y: 1200 });
```

```ts
await sb.control("key", { name: "back" });
```

#### `sb.tap(x: number, y: number): Promise<unknown>`

Tap at device pixel coordinates.

```ts
await sb.tap(540, 1200);
```

#### `sb.swipe(x1, y1, x2, y2, ms = 300): Promise<unknown>`

Swipe from `(x1, y1)` to `(x2, y2)` over `ms` milliseconds.

```ts
await sb.swipe(540, 1800, 540, 400);
```

```ts
await sb.swipe(100, 1000, 900, 1000, 800);
```

#### `sb.key(name: string): Promise<unknown>`

Press a hardware/navigation key (`home`, `back`, `enter`, `power`, …).

```ts
await sb.key("home");
```

#### `sb.text(text: string): Promise<unknown>`

Type into the focused field.

```ts
await sb.tapText("Email");
await sb.text("qa@example.com");
```

#### `sb.tapText(text: string): Promise<unknown>`

Tap the on-screen element whose label matches `text`.

```ts
await sb.tapText("Sign in");
```

#### `sb.launch(app: string): Promise<unknown>`

Launch an app by package id (Android) or bundle id (iOS).

```ts
await sb.launch("com.android.settings");
```

```ts
await sb.launch("com.apple.Preferences");
```

#### `sb.launchIntent(pkg, component, opts?): Promise<unknown>`

Start an exported Android activity with optional `action`, `data` URI and string `extras`.

```ts
await sb.launchIntent("com.example.app", ".MainActivity");
```

```ts
await sb.launchIntent("com.example.app", "com.example.app.DeepLinkActivity", {
  action: "android.intent.action.VIEW",
  data: "example://orders/42",
  extras: { source: "ci" },
});
```

### Inspection

#### `sb.screenshot(): Promise<Uint8Array>`

A PNG/JPEG screenshot.

```ts
import { writeFile } from "node:fs/promises";

await writeFile("screen.png", await sb.screenshot());
```

```ts
const png = await sb.screenshot();
const url = URL.createObjectURL(new Blob([png as BlobPart], { type: "image/png" }));
img.src = url;
```

#### `sb.describeUi(): Promise<unknown>`

The accessibility/UI tree.

```ts
console.log(JSON.stringify(await sb.describeUi(), null, 2));
```

#### `sb.metrics(): Promise<unknown>`

Live CPU/memory/battery/uptime.

```ts
console.log(await sb.metrics());
```

#### `sb.storage(): Promise<unknown>`

Disk-usage breakdown.

```ts
console.log(await sb.storage());
```

#### `sb.exportAvd(destPath: string, opts?: { timeoutMs?: number }): Promise<Record<string, unknown>>`

**Node only.** Export this Android sandbox's AVD as a portable profile `.tar` to
`destPath`, for sharing or for `templates.importAvd()` onto another node. **Stop
the device first.** Resolves to the profile metadata (`filename`, `size_bytes`,
`system_image`, …) plus `savedTo` and `bytes`.

```ts
await sb.stop();
const meta = await sb.exportAvd("golden-pixel.tar");
console.log(meta.system_image, meta.bytes);
```

### Live channels

Each returns a [`Channel`](#channel). Iterate with `for await`; breaking out closes the socket.

#### `sb.logs(): Channel<string>`

Stream device logs.

```ts
for await (const line of sb.logs()) console.log(line);
```

```ts
for await (const line of sb.logs()) {
  if (line.includes("FATAL EXCEPTION")) break;
}
```

#### `sb.shell(): Channel<string>`

Interactive shell; send keystrokes with `.send()`.

```ts
const sh = sb.shell();
await sh.send("getprop ro.build.version.release\n");
for await (const out of sh) {
  process.stdout.write(out);
}
```

#### `sb.screen(opts?: { source?: "host" | "scrcpy" }): Channel<Uint8Array>`

Raw binary screen frames (default `source: "scrcpy"`).

```ts
for await (const frame of sb.screen()) console.log(frame.byteLength);
```

```ts
const ch = sb.screen({ source: "host" });
```

#### `sb.screenWebrtc(): Channel<unknown>`

WebRTC signaling (SDP/ICE JSON). The browser is the media peer.

```ts
const sig = sb.screenWebrtc();
sig.on("message", (msg) => handleSignal(msg));
```

#### `sb.webrtcPlayerUrl(): string`

Signaling URL (token included) to hand to a browser WebRTC player.

```ts
console.log(sb.webrtcPlayerUrl());
```

#### `sb.adb(): Channel<Uint8Array>`

Raw adb transport bytes.

```ts
const adb = sb.adb();
await adb.ready;
```

#### `sb.vnc(): Channel<Uint8Array>`

Raw RFB (VNC) bytes. iOS VM only.

```ts
for await (const chunk of sb.vnc()) rfbClient.feed(chunk);
```

#### `sb.gdb(): Channel<Uint8Array>`

Raw gdb-remote bytes to the guest-kernel gdb stub. Cuttlefish debug sandboxes only.

```ts
const gdb = sb.gdb();
await gdb.send(new TextEncoder().encode("$qSupported#37"));
```

#### `sb.console(opts?: { process?: string }): Channel<string>`

lldb debugger console stream.

```ts
const c = sb.console({ process: "com.example.app" });
await c.send("bt\n");
```

#### `sb.mitmFlows(): Channel<unknown>`

Captured HTTP(S) flow summaries as JSON (`method`, `scheme`, `host`, `path`, `status`, `content_type`, …). Capture must be started for the sandbox in the console.

```ts
for await (const flow of sb.mitmFlows()) {
  const f = flow as { method: string; status: number | null; host: string; path: string };
  console.log(f.method, f.status, f.host + f.path);
}
```

#### `sb.mitmCa(): Promise<Uint8Array>`

The mitmproxy CA certificate (PEM). Rejects with `ApiError` (404) until capture has run once.

```ts
import { writeFile } from "node:fs/promises";

await writeFile("orchard-ca.pem", await sb.mitmCa());
```

## sb.files

### `files.list(path = ""): Promise<unknown>`

List a device directory (default: the platform home).

```ts
console.log(await sb.files.list());
```

```ts
console.log(await sb.files.list("/sdcard/Download"));
```

### `files.download(path: string): Promise<Uint8Array>`

Download a device file via a short-lived signed grant.

```ts
import { writeFile } from "node:fs/promises";

await writeFile("app.db", await sb.files.download("/data/data/com.example.app/databases/app.db"));
```

### `files.upload(file: Uploadable, path?: string): Promise<unknown>`

Upload a `File`/`Blob` into a device directory.

```ts
import { openAsBlob } from "node:fs";

const blob = await openAsBlob("./fixtures/photo.jpg");
await sb.files.upload(Object.assign(blob, { name: "photo.jpg" }), "/sdcard/Pictures");
```

```ts
await sb.files.upload(input.files![0], "/sdcard/Download");
```

## sb.apps

### `apps.list(): Promise<unknown>`

Installed apps/packages.

```ts
console.log(await sb.apps.list());
```

### `apps.install(...files: Uploadable[]): Promise<unknown>`

Install an `.apk`/`.ipa`; pass several parts for a split-APK set.

```ts
import { openAsBlob } from "node:fs";

const apk = Object.assign(await openAsBlob("./build/app.apk"), { name: "app.apk" });
await sb.apps.install(apk);
```

```ts
import { openAsBlob } from "node:fs";

const parts = await Promise.all(
  ["base.apk", "split_config.arm64_v8a.apk"].map(async (n) => Object.assign(await openAsBlob(`./splits/${n}`), { name: n })),
);
await sb.apps.install(...parts);
```

### `apps.uninstall(pkg: string): Promise<unknown>`

Uninstall by package id.

```ts
await sb.apps.uninstall("com.example.app");
```

### `apps.download(pkg: string): Promise<Uint8Array>`

Pull an installed app's APK(s) via a signed grant.

```ts
import { writeFile } from "node:fs/promises";

await writeFile("settings.apk", await sb.apps.download("com.android.settings"));
```

### `apps.launch(pkg: string): Promise<unknown>`

Launch an installed app.

```ts
await sb.apps.launch("com.example.app");
```

## sb.frida

Requires capability `frida`. `inject` and `stream` are Android only.

### `frida.status(): Promise<unknown>`

frida-server state (installed/running/version/port).

```ts
console.log(await sb.frida.status());
```

### `frida.install(): Promise<unknown>`

Install frida-server (slow) and start it.

```ts
await sb.frida.install();
```

### `frida.start(): Promise<unknown>`

Start frida-server.

```ts
await sb.frida.start();
```

### `frida.stop(): Promise<unknown>`

Stop frida-server.

```ts
await sb.frida.stop();
```

### `frida.verify(process?: string): Promise<unknown>`

Attach and trace a process to prove frida works; returns the collected `messages`.

```ts
console.log(await sb.frida.verify());
```

```ts
console.log(await sb.frida.verify("com.example.app"));
```

### `frida.inject(script: string, process: string, timeout = 6.0): Promise<unknown>`

Run a script for `timeout` seconds (1–30), then detach; returns `send()`/`console` output as `messages`.

```ts
const res = await sb.frida.inject(`send(Process.id);`, "com.example.app");
```

```ts
import { readFile } from "node:fs/promises";

const res = await sb.frida.inject(await readFile("hooks/ssl.js", "utf8"), "com.example.app", 20);
```

### `frida.stream(script: string, process: string, timeout = 0): Channel<unknown>`

Run a script and stream each message as it arrives. `timeout <= 0` streams until you close the channel.

```ts
const script = `Interceptor.attach(Module.getExportByName(null, "open"), { onEnter(a) { send(a[0].readUtf8String()); } });`;
for await (const msg of sb.frida.stream(script, "com.example.app")) console.log(msg);
```

```ts
const ch = sb.frida.stream(script, "com.example.app", 15);
ch.on("message", console.log).on("close", () => console.log("done"));
```

## sb.debugger

Needs a rootable image for ptrace; on Cuttlefish use a debug sandbox.

### `debugger.status(): Promise<unknown>`

lldb-server state (installed/running/port).

```ts
console.log(await sb.debugger.status());
```

### `debugger.install(): Promise<unknown>`

Push lldb-server to the device (needs root) and start it.

```ts
await sb.debugger.install();
```

### `debugger.start(process?: string): Promise<unknown>`

Start lldb-server, optionally attached to `process`.

```ts
await sb.debugger.start();
```

```ts
await sb.debugger.start("com.example.app");
```

### `debugger.console(process?: string): Channel<string>`

Interactive lldb console; send commands with `.send()`.

```ts
const lldb = sb.debugger.console("com.example.app");
await lldb.send("bt\n");
for await (const line of lldb) console.log(line);
```

## sb.snapshots

### `snapshots.list(): Promise<SnapshotRow[]>`

This sandbox's snapshots.

```ts
for (const s of await sb.snapshots.list()) console.log(s.name, s.created_at);
```

### `snapshots.create(name: string): Promise<unknown>`

Take a snapshot.

```ts
await sb.snapshots.create("clean-install");
```

### `snapshots.restore(name: string): Promise<unknown>`

Restore to a snapshot.

```ts
await sb.snapshots.restore("clean-install");
```

### `snapshots.delete(name: string): Promise<unknown>`

Delete a snapshot.

```ts
await sb.snapshots.delete("clean-install");
```

### `snapshots.saveAsTemplate(opts): Promise<SnapshotRow>`

Save the sandbox (or one snapshot) as a template. `opts`: `name`, `visibility?` (`"private"` | `"org"`, default `"private"`), `description?`, `snapshot?`.

```ts
await sb.snapshots.saveAsTemplate({ name: "pixel-logged-in" });
```

```ts
await sb.snapshots.saveAsTemplate({ name: "pixel-baseline", visibility: "org", description: "Fresh image + test app", snapshot: "clean-install" });
```

## orchard.snapshots

### `snapshots.list(): Promise<SnapshotRow[]>`

Every point snapshot in the org/workspace.

```ts
for (const s of await orchard.snapshots.list()) console.log(s.instance_uuid, s.name);
```

## orchard.templates

### `templates.list(): Promise<SnapshotRow[]>`

Available templates.

```ts
const templates = await orchard.templates.list();
```

### `templates.delete(pk: number): Promise<unknown>`

Delete a template by id.

```ts
await orchard.templates.delete(12);
```

### `templates.launch(pk: number, name: string, spec?: Record<string, unknown>): Promise<unknown>`

Launch a new sandbox from a template.

```ts
await orchard.templates.launch(12, "ci-run-481");
```

```ts
const t = (await orchard.templates.list()).find((t) => t.name === "pixel-baseline")!;
await orchard.templates.launch(t.id, "ci-run-482", { cpu: 4 });
```

### `templates.importAvd(path: string, name: string, opts: { node: string; provider?: string; installImage?: boolean; timeoutMs?: number }): Promise<SnapshotRow>`

**Node only.** Import a portable AVD profile `.tar` (from `sb.exportAvd()`) onto
`opts.node` as a new, launchable template. The file is streamed **directly from
this machine to the node** — the control plane only authorizes and records it, so
a multi-GB profile is never buffered in the backend. This machine must be able to
reach the node's agent. Set `installImage: true` to fetch the base system image
if the node is missing it.

```ts
const row = await orchard.templates.importAvd("golden-pixel.tar", "Golden Pixel", { node: "mac-ios" });
await orchard.templates.launch(row.id, "from-golden");
```

## orchard.catalog

### `catalog.android(): Promise<unknown>`

Android system images and device profiles.

```ts
console.log(await orchard.catalog.android());
```

### `catalog.presets(): Promise<unknown>`

iOS patch presets.

```ts
console.log(await orchard.catalog.presets());
```

### `catalog.simDeviceTypes(): Promise<unknown>`

iOS simulator device types and runtimes.

```ts
console.log(await orchard.catalog.simDeviceTypes());
```

### `catalog.providers(): Promise<unknown>`

Per-node provider availability (platform admin only).

```ts
console.log(await orchard.catalog.providers());
```

## orchard.jobs

### `jobs.list(): Promise<Job[]>`

Background jobs (image downloads, VM creates).

```ts
for (const j of await orchard.jobs.list()) console.log(j.kind, j.target, j.state, j.progress);
```

### `jobs.cancel(node: string, jobId: string): Promise<unknown>`

Cancel a running job.

```ts
const job = (await orchard.jobs.list()).find((j) => j.state === "running")!;
await orchard.jobs.cancel(job.node, job.id);
```

### `jobs.logs(node: string, kind: string, name: string): Channel<string>`

Stream a job's log lines.

```ts
for await (const line of orchard.jobs.logs(job.node, job.kind, job.target)) console.log(line);
```

## orchard.nodes

Mostly platform admin.

### `nodes.list(): Promise<unknown[]>`

Placeable nodes.

```ts
console.log(await orchard.nodes.list());
```

### `nodes.create(cfg: Record<string, unknown>): Promise<unknown>`

Enroll a node (`name`, `agent_url`, `agent_token`).

```ts
await orchard.nodes.create({ name: "mac-mini-2", agent_url: "https://10.0.0.12:7070", agent_token: "…" });
```

### `nodes.test(cfg: Record<string, unknown>): Promise<unknown>`

Probe an agent URL + token before enrolling.

```ts
await orchard.nodes.test({ agent_url: "https://10.0.0.12:7070", agent_token: "…" });
```

### `nodes.refresh(pk: number): Promise<unknown>`

Re-poll one node.

```ts
await orchard.nodes.refresh(3);
```

### `nodes.delete(pk: number): Promise<unknown>`

Remove a node.

```ts
await orchard.nodes.delete(3);
```

## orchard.keys

### `keys.list(): Promise<ApiKey[]>`

Your API keys (metadata only).

```ts
for (const k of await orchard.keys.list()) console.log(k.id, k.name, k.hint, k.expires_at);
```

### `keys.create(name: string, opts?): Promise<ApiKey>`

Mint a key; the secret is in `token`, shown once. `opts`: `sandboxUuids?`, `tag?` (every sandbox with that tag, now and future), `allowedFeatures?`, `expiresInDays?`. Omit all scope options for an org-wide key.

```ts
const key = await orchard.keys.create("ci", { sandboxUuids: [sb.uuid], allowedFeatures: ["logs", "files"], expiresInDays: 30 });
console.log(key.token);
```

```ts
const key = await orchard.keys.create("payments-team", { tag: "payments" });
```

### `keys.delete(id: number): Promise<unknown>`

Revoke a key.

```ts
await orchard.keys.delete(key.id);
```

## orchard.team

### `team.get(): Promise<unknown>`

The org, its usage, features and member count.

```ts
console.log(await orchard.team.get());
```

### `team.edit(fields: Record<string, unknown>): Promise<unknown>`

Change org fields (org admin).

```ts
await orchard.team.edit({ name: "Acme Mobile" });
```

### `team.inviteInfo(token: string): Promise<unknown>`

Describe an invite token.

```ts
console.log(await orchard.team.inviteInfo("inv_9f2c…"));
```

### `team.acceptInvite(token: string, account?: Record<string, unknown>): Promise<unknown>`

Accept an invite, optionally creating an account.

```ts
await orchard.team.acceptInvite("inv_9f2c…");
```

```ts
await orchard.team.acceptInvite("inv_9f2c…", { username: "sam", password: "…", email: "sam@example.com" });
```

### `team.members.list(): Promise<unknown[]>`

Org members.

```ts
console.log(await orchard.team.members.list());
```

### `team.members.edit(pk: number, fields: Record<string, unknown>): Promise<unknown>`

Change a member's `role`, `denied_features` or limits.

```ts
await orchard.team.members.edit(7, { role: "admin" });
```

```ts
await orchard.team.members.edit(7, { denied_features: ["shell", "frida"] });
```

### `team.members.remove(pk: number): Promise<unknown>`

Remove a member.

```ts
await orchard.team.members.remove(7);
```

### `team.invites.list(): Promise<unknown[]>`

Pending invites.

```ts
console.log(await orchard.team.invites.list());
```

### `team.invites.create(role = "member"): Promise<{ token: string; expires_at: string }>`

Create an invite; `token` is the one-time join credential.

```ts
const { token, expires_at } = await orchard.team.invites.create();
```

```ts
const admin = await orchard.team.invites.create("admin");
```

### `team.invites.delete(pk: number): Promise<unknown>`

Revoke an invite.

```ts
await orchard.team.invites.delete(4);
```

## orchard.workspaces

### `workspaces.list(): Promise<unknown[]>`

Your workspaces.

```ts
console.log(await orchard.workspaces.list());
```

### `workspaces.create(name: string, slug?: string): Promise<unknown>`

Create a workspace (org admin).

```ts
await orchard.workspaces.create("QA");
```

```ts
await orchard.workspaces.create("Payments QA", "payments-qa");
```

### `workspaces.get(slug: string): Workspace`

A handle to one workspace. Has `slug`, `edit`, `delete`, `members` and `invites` (same methods as `team.members` / `team.invites`).

```ts
const qa = orchard.workspaces.get("qa");
```

### `workspace.edit(fields: Record<string, unknown>): Promise<unknown>`

Change workspace fields.

```ts
await orchard.workspaces.get("qa").edit({ name: "QA Lab" });
```

### `workspace.delete(): Promise<unknown>`

Delete the workspace (must be empty; not the default).

```ts
await orchard.workspaces.get("qa").delete();
```

### `workspace.members` / `workspace.invites`

Members and invites scoped to the workspace.

```ts
const qa = orchard.workspaces.get("qa");
console.log(await qa.members.list());
const { token } = await qa.invites.create("member");
```

## orchard.remote

Cloud sandboxes (e2b / daytona / modal). `ref` is a uuid or numeric record id.

### `remote.credentials(): Promise<unknown[]>`

Stored provider credentials.

```ts
console.log(await orchard.remote.credentials());
```

### `remote.addCredential(provider: string, key: string, extra?: Record<string, unknown>): Promise<unknown>`

Store and verify a provider API key.

```ts
await orchard.remote.addCredential("e2b", process.env.E2B_API_KEY!);
```

```ts
await orchard.remote.addCredential("daytona", process.env.DAYTONA_API_KEY!, { label: "prod", config: { region: "us" } });
```

### `remote.deleteCredential(pk: number): Promise<unknown>`

Delete a credential.

```ts
await orchard.remote.deleteCredential(2);
```

### `remote.catalog(): Promise<unknown>`

Which providers are available/configured.

```ts
console.log(await orchard.remote.catalog());
```

### `remote.create(provider: string, name: string, spec?: Record<string, unknown>): Promise<unknown>`

Create a remote sandbox (`image`, `cpu`, `memory_mb`, `region`, `ttl_minutes`, …).

```ts
const box = await orchard.remote.create("e2b", "scratch");
```

```ts
const box = await orchard.remote.create("daytona", "build-box", { cpu: 4, memory_mb: 8192, ttl_minutes: 60 });
```

### `remote.get(ref: number | string): Promise<unknown>`

Fetch a remote sandbox.

```ts
console.log(await orchard.remote.get("6f1c2d9e-…"));
```

### `remote.delete(ref: number | string): Promise<unknown>`

Terminate it.

```ts
await orchard.remote.delete(14);
```

### `remote.start(ref: number | string): Promise<unknown>`

Start it.

```ts
await orchard.remote.start(14);
```

### `remote.stop(ref: number | string): Promise<unknown>`

Stop it.

```ts
await orchard.remote.stop(14);
```

### `remote.shell(ref: number | string): Channel<string>`

Interactive shell.

```ts
const sh = orchard.remote.shell(14);
await sh.send("uname -a\n");
for await (const out of sh) process.stdout.write(out);
```

### `remote.upload(ref, data: Uint8Array | Blob, path?: string, filename = "upload"): Promise<unknown>`

Upload bytes or a `File`/`Blob`.

```ts
await orchard.remote.upload(14, new TextEncoder().encode("hello\n"), "/tmp", "hello.txt");
```

```ts
import { readFile } from "node:fs/promises";

await orchard.remote.upload(14, await readFile("./script.sh"), "/home/user", "script.sh");
```

### `remote.download(ref: number | string, path: string): Promise<Uint8Array>`

Download a file's bytes.

```ts
const text = new TextDecoder().decode(await orchard.remote.download(14, "/tmp/hello.txt"));
```

### `remote.logs(ref: number | string): Channel<string>`

Stream logs.

```ts
for await (const line of orchard.remote.logs(14)) console.log(line);
```

### `remote.metrics(ref: number | string): Promise<unknown>`

Live CPU/memory/uptime sample.

```ts
console.log(await orchard.remote.metrics(14));
```

## Channel

`Channel<T>` is a live WebSocket stream. It opens on creation.

### `channel.ready: Promise<void>`

Resolves when the socket opens; rejects if it fails.

```ts
const logs = sb.logs();
await logs.ready;
```

### `for await (const item of channel)`

Iterate decoded frames. `break` closes the channel; an Orchard close code rejects with `ChannelClosedError`.

```ts
for await (const line of sb.logs()) console.log(line);
```

### `channel.on(event: "message" | "open" | "close" | "error", cb): this`

Event-emitter style consumption.

```ts
sb.logs()
  .on("open", () => console.log("connected"))
  .on("message", (line) => console.log(line))
  .on("close", () => console.log("closed"));
```

### `channel.send(data: string | ArrayBufferView): Promise<void>`

Send a frame upstream; waits for the socket to open.

```ts
await sb.shell().send("ls /sdcard\n");
```

### `channel.close(): void`

Close the channel.

```ts
const logs = sb.logs();
setTimeout(() => logs.close(), 10_000);
for await (const line of logs) console.log(line);
```

## Selectors

Precedence: exact uuid, uuid prefix, exact `name`/`display_name`, then `tag`. The first tier that matches wins.

### `resolve(instances: Instance[], selector: string): Instance`

Exactly one match, or throw `SelectorError`.

```ts
import { resolve } from "@tryorchard/sdk";

const { instances } = await orchard.sandboxes.list();
const inst = resolve(instances, "my-pixel");
```

### `resolveAll(instances: Instance[], selector: string): Instance[]`

Every match in the first tier that hits.

```ts
import { resolveAll } from "@tryorchard/sdk";

const tagged = resolveAll(instances, "payments");
```

## Errors

All extend `OrchardError`.

| Class | Thrown when | Fields |
| --- | --- | --- |
| `ApiError` | REST response ≥ 400 | `status`, `detail` |
| `SelectorError` | selector matched zero or several sandboxes | — |
| `ChannelClosedError` | channel closed with an Orchard code | `code`, `reason` |

| Close code | Meaning |
| --- | --- |
| `4401` | unauthenticated |
| `4403` | forbidden |
| `4404` | not found |
| `4502` | upstream agent unreachable |

```ts
import { ApiError, SelectorError } from "@tryorchard/sdk";

try {
  await (await orchard.sandbox("my-pixel")).start();
} catch (e) {
  if (e instanceof SelectorError) console.error(e.message);
  else if (e instanceof ApiError && e.status === 403) console.error("key lacks access:", e.detail);
  else throw e;
}
```

```ts
import { ChannelClosedError } from "@tryorchard/sdk";

try {
  for await (const line of sb.shell()) console.log(line);
} catch (e) {
  if (e instanceof ChannelClosedError && e.code === 4403) console.error("shell not allowed for this key");
}
```

## Types

| Type | Description |
| --- | --- |
| `OrchardOptions` | Constructor options. |
| `ResolvedConfig` | `{ url, token, org?, ws?, timeout }`. |
| `Instance` | A sandbox row (`uuid`, `name`, `state`, `platform`, `provider`, `tag`, `capabilities`, `hardware`, `runtime`, …). |
| `InstanceList` | `{ instances: Instance[]; errors: { node, detail }[] }`. |
| `Capability` | `{ key, supported, available, reason }`. |
| `SnapshotRow` | A snapshot or template (`id`, `name`, `kind`, `visibility`, `instance_uuid`, …). |
| `Job` | A background job (`id`, `node`, `kind`, `target`, `state`, `progress`, …). |
| `ApiKey` | A key row; `token` only on create. |
| `LogLine` | `{ ts?, source?, text }`. |
| `FlowEvent` | A captured flow summary (`Record<string, unknown>`). |
| `Platform` | `"ios" \| "android"`. |
| `Provider` | `"vphone" \| "baguette" \| "android" \| "cuttlefish" \| "qemu" \| "e2b" \| "daytona" \| "modal"`. |
| `Uploadable` | `Blob & { name?: string }` — a browser `File` or a named `Blob`. |
