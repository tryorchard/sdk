/** Sandboxes namespace + the {@link Sandbox} handle. @packageDocumentation */
import type { ResolvedConfig } from "../config.js";
import type { Http } from "../http.js";
import type { ApiKey, Instance, InstanceList, SnapshotRow } from "../models.js";
import { resolve, resolveAll } from "../selector.js";
import {
  Channel,
  channelUrl,
  decodeBytes,
  decodeJson,
  decodeText,
} from "../ws.js";

/** A file to upload: a browser `File`, or any `Blob` (give Node Blobs a name). */
export type Uploadable = Blob & { name?: string };

function appendFile(form: FormData, field: string, f: Uploadable): void {
  form.append(field, f, f.name ?? "upload.bin");
}

/** `orchard.sandboxes` — fleet-wide listing and creation. */
export class Sandboxes {
  constructor(
    private readonly http: Http,
    private readonly cfg: ResolvedConfig,
  ) {}

  /** List every sandbox visible to this key/org. */
  list(): Promise<InstanceList> {
    return this.http.get<InstanceList>("/instances");
  }

  /** Create a sandbox (platform/name/cpu/memory_mb + platform fields). */
  create(spec: Record<string, unknown>): Promise<Instance> {
    return this.http.post<Instance>("/instances/create", spec);
  }

  /** Create an iOS simulator sandbox (name/device_type/runtime). */
  createSim(spec: Record<string, unknown>): Promise<Instance> {
    return this.http.post<Instance>("/instances/create-sim", spec);
  }

  /** Resolve a selector (uuid / uuid-prefix / name / tag) to one instance. */
  async resolve(selector: string): Promise<Instance> {
    return resolve((await this.list()).instances, selector);
  }

  /** Every instance a selector matches (tags match many). */
  async resolveAll(selector: string): Promise<Instance[]> {
    return resolveAll((await this.list()).instances, selector);
  }

  /** A {@link Sandbox} handle for a known uuid (no lookup). */
  get(uuid: string): Sandbox {
    return new Sandbox(this.http, this.cfg, uuid);
  }
}

/** A handle to one sandbox, addressed by uuid. */
export class Sandbox {
  private readonly base: string;
  /** Files on the device. */
  readonly files: Files;
  /** Apps on the device. */
  readonly apps: Apps;
  /** This sandbox's snapshots. */
  readonly snapshots: SandboxSnapshots;
  /** frida-server and script injection on the device. */
  readonly frida: Frida;
  /** On-device lldb (lldb-server + attach). */
  readonly debugger: Debugger;

  constructor(
    private readonly http: Http,
    private readonly cfg: ResolvedConfig,
    readonly uuid: string,
  ) {
    this.base = `/sandboxes/${uuid}`;
    this.files = new Files(http, cfg, uuid);
    this.apps = new Apps(http, cfg, uuid);
    this.snapshots = new SandboxSnapshots(http, uuid);
    this.frida = new Frida(http, cfg, uuid);
    this.debugger = new Debugger(http, cfg, uuid);
  }

  /** Fetch the full instance dict. */
  get(): Promise<Instance> {
    return this.http.get<Instance>(this.base);
  }

  start(): Promise<unknown> {
    return this.http.post(`${this.base}/start`);
  }

  stop(): Promise<unknown> {
    return this.http.post(`${this.base}/stop`);
  }

  /** Terminate the sandbox (deletes its disk). */
  delete(): Promise<unknown> {
    return this.http.del(this.base);
  }

  /** Change metadata/size. cpu/memory_mb require the sandbox stopped; owner requires org admin. */
  edit(patch: {
    notes?: string;
    tag?: string;
    tag_color?: string;
    owner?: string;
    cpu?: number;
    memory_mb?: number;
  }): Promise<Instance> {
    return this.http.patch<Instance>(this.base, patch);
  }

  /** Set the tag (and optional `#rrggbb` chip colour). */
  tag(tag: string, color?: string): Promise<Instance> {
    return this.http.patch<Instance>(this.base, color ? { tag, tag_color: color } : { tag });
  }

  /** Unified input action (tap/swipe/key/text/launch/tap_text). */
  control(action: string, extra: Record<string, unknown> = {}): Promise<unknown> {
    return this.http.post(`${this.base}/control`, { action, ...extra });
  }

  /** Tap (click) at device pixel coordinates `(x, y)`. */
  tap(x: number, y: number): Promise<unknown> {
    return this.control("tap", { x, y });
  }

  /** Swipe/drag from `(x1,y1)` to `(x2,y2)` over `ms` milliseconds (default 300). */
  swipe(x1: number, y1: number, x2: number, y2: number, ms = 300): Promise<unknown> {
    return this.control("swipe", { x1, y1, x2, y2, ms });
  }

  /** Press a hardware/navigation key (e.g. `home`, `back`, `enter`, `power`). */
  key(name: string): Promise<unknown> {
    return this.control("key", { name });
  }

  /** Type `text` into the focused field. */
  text(text: string): Promise<unknown> {
    return this.control("text", { text });
  }

  /** Find an on-screen element whose label matches `text` and tap it. */
  tapText(text: string): Promise<unknown> {
    return this.control("tap_text", { text });
  }

  /** Launch an app by package id (Android) or bundle id (iOS). */
  launch(app: string): Promise<unknown> {
    return this.control("launch", { app });
  }

  /**
   * Start an exported activity `component` in `package` (Android), with an
   * optional intent `action`, `data` URI and string `extras`. The activity must
   * be exported, or the device refuses the launch.
   */
  launchIntent(
    pkg: string,
    component: string,
    opts: { action?: string; data?: string; extras?: Record<string, string> } = {},
  ): Promise<unknown> {
    return this.control("launch_intent", {
      package: pkg,
      component,
      intent_action: opts.action,
      data: opts.data,
      extras: opts.extras,
    });
  }

  /** A PNG/JPEG screenshot. */
  screenshot(): Promise<Uint8Array> {
    return this.http.getBytes(`${this.base}/screenshot`);
  }

  describeUi(): Promise<unknown> {
    return this.http.get(`${this.base}/describe-ui`);
  }

  metrics(): Promise<unknown> {
    return this.http.get(`${this.base}/metrics`);
  }

  storage(): Promise<unknown> {
    return this.http.get(`${this.base}/storage`);
  }

  /** Export this Android sandbox's AVD as a portable profile `.tar` to `destPath`
   * (Node only), for sharing or for {@link Templates.importAvd} onto another node.
   * **Stop the device first.** Resolves to the profile metadata (`filename`,
   * `size_bytes`, `system_image`, …) plus `savedTo` and `bytes`. */
  async exportAvd(destPath: string, opts: { timeoutMs?: number } = {}): Promise<Record<string, unknown>> {
    const meta = await this.http.post<Record<string, unknown>>(`${this.base}/avd/export`);
    const bytes = await this.http.streamToFile(
      `${this.base}/avd/export/${meta.filename}`, destPath, opts.timeoutMs);
    return { ...meta, savedTo: destPath, bytes };
  }

  // -- live channels --
  /** Stream logs: `for await (const line of sb.logs()) …`. */
  logs(): Channel<string> {
    return new Channel(channelUrl(this.cfg, this.uuid, "logs"), decodeText);
  }

  /** An interactive shell stream (`.send()` keystrokes). */
  shell(): Channel<string> {
    return new Channel(channelUrl(this.cfg, this.uuid, "shell"), decodeText);
  }

  /** Raw screen frames (binary). `source` is `host` or `scrcpy`. */
  screen(opts: { source?: "host" | "scrcpy" } = {}): Channel<Uint8Array> {
    return new Channel(
      channelUrl(this.cfg, this.uuid, "screen/stream", { source: opts.source ?? "scrcpy" }),
      decodeBytes,
    );
  }

  /** WebRTC screen signaling (SDP/ICE JSON). The browser is the media peer; to
   * view, open {@link webrtcPlayerUrl} in the console or the standalone player. */
  screenWebrtc(): Channel<unknown> {
    return new Channel(channelUrl(this.cfg, this.uuid, "screen/webrtc"), decodeJson);
  }

  /** The control-plane WebRTC signaling URL to hand to a browser player. */
  webrtcPlayerUrl(): string {
    return channelUrl(this.cfg, this.uuid, "screen/webrtc");
  }

  /** Raw adb transport bytes. */
  adb(): Channel<Uint8Array> {
    return new Channel(channelUrl(this.cfg, this.uuid, "adb"), decodeBytes);
  }

  /** Raw RFB (VNC) bytes — iOS VM only. */
  vnc(): Channel<Uint8Array> {
    return new Channel(channelUrl(this.cfg, this.uuid, "vnc"), decodeBytes);
  }

  /**
   * Raw gdb-remote bytes to a sandbox's guest-kernel gdb stub. Bridge to a local
   * port, then `gdb-multiarch vmlinux` and `target remote` (or lldb). Cuttlefish
   * debug sandboxes, Android emulators and iOS VMs launched with kernel debugging
   * (capability `kernel-debug`).
   */
  gdb(): Channel<Uint8Array> {
    return new Channel(channelUrl(this.cfg, this.uuid, "gdb"), decodeBytes);
  }

  /** lldb debugger console stream. */
  console(opts: { process?: string } = {}): Channel<string> {
    return new Channel(
      channelUrl(this.cfg, this.uuid, "debugger/console", { process: opts.process }),
      decodeText,
    );
  }

  /** Captured HTTP(S) flow summaries (JSON). */
  mitmFlows(): Channel<unknown> {
    return new Channel(channelUrl(this.cfg, this.uuid, "mitm/flows"), decodeJson);
  }

  /** The mitmproxy CA certificate (PEM bytes). */
  mitmCa(): Promise<Uint8Array> {
    return this.http.getBytes(`${this.base}/mitm/ca`);
  }
}

/** `sandbox.files` — list, download and upload device files. */
export class Files {
  private readonly base: string;
  constructor(
    private readonly http: Http,
    private readonly cfg: ResolvedConfig,
    uuid: string,
  ) {
    this.base = `/sandboxes/${uuid}`;
  }

  list(path = ""): Promise<unknown> {
    return this.http.get(`${this.base}/files`, path ? { path } : undefined);
  }

  /** Download a device file via a short-lived signed grant → bytes. */
  async download(path: string): Promise<Uint8Array> {
    const grant = await this.http.post<{ url: string }>(`${this.base}/files/grant`, { path });
    return this.http.download(this.http.absolute(grant.url));
  }

  /** Upload a file into device directory `path`. */
  upload(file: Uploadable, path?: string): Promise<unknown> {
    const form = new FormData();
    appendFile(form, "file", file);
    if (path) form.append("path", path);
    return this.http.postForm(`${this.base}/files/upload`, form);
  }
}

/** `sandbox.apps` — list, install, uninstall and pull apps. */
export class Apps {
  private readonly base: string;
  constructor(
    private readonly http: Http,
    private readonly cfg: ResolvedConfig,
    uuid: string,
  ) {
    this.base = `/sandboxes/${uuid}`;
  }

  list(): Promise<unknown> {
    return this.http.get(`${this.base}/apps`);
  }

  /** Install an `.apk`/`.ipa` (pass several parts for a split-APK set). */
  install(...files: Uploadable[]): Promise<unknown> {
    const form = new FormData();
    for (const f of files) appendFile(form, "file", f);
    return this.http.postForm(`${this.base}/apps/install`, form);
  }

  uninstall(pkg: string): Promise<unknown> {
    return this.http.post(`${this.base}/apps/uninstall`, { package: pkg });
  }

  /** Pull an installed app's APK(s) via a signed grant → bytes. */
  async download(pkg: string): Promise<Uint8Array> {
    const grant = await this.http.post<{ url: string }>(`${this.base}/apps/grant`, { package: pkg });
    return this.http.download(this.http.absolute(grant.url));
  }

  launch(pkg: string): Promise<unknown> {
    return this.http.post(`${this.base}/control`, { action: "launch", app: pkg });
  }
}

/**
 * `sandbox.frida` — frida-server and script injection on the device.
 *
 * All methods go through `POST /sandboxes/<uuid>/frida` (capability `frida`).
 * `inject` is Android only today; `verify` runs the Stalker check on iOS.
 */
export class Frida {
  private readonly base: string;
  constructor(
    private readonly http: Http,
    private readonly cfg: ResolvedConfig,
    private readonly uuid: string,
  ) {
    this.base = `/sandboxes/${uuid}/frida`;
  }

  /** Report frida-server state (installed/running/version/port). */
  status(): Promise<unknown> {
    return this.http.get(this.base);
  }

  /** Install frida-server (slow; pulls packages) and start it. */
  install(): Promise<unknown> {
    return this.http.post(this.base, { action: "install" });
  }

  /** Start frida-server. */
  start(): Promise<unknown> {
    return this.http.post(this.base, { action: "start" });
  }

  /** Stop frida-server. */
  stop(): Promise<unknown> {
    return this.http.post(this.base, { action: "stop" });
  }

  /** Attach and trace a process to prove frida works; returns the script `messages`. */
  verify(process?: string): Promise<unknown> {
    return this.http.post(this.base, { action: "verify", process });
  }

  /**
   * Run a frida `script` against `process` for `timeout` seconds (1-30), then
   * detach. Returns the script's `send()`/`console` output as `messages`.
   * Android only.
   */
  inject(script: string, process: string, timeout = 6.0): Promise<unknown> {
    return this.http.post(this.base, { action: "inject", script, process, timeout });
  }

  /**
   * Run a frida `script` against `process` and stream each message as it
   * arrives, instead of collecting them. Returns a {@link Channel} of frida
   * messages. `timeout` <= 0 streams until you close the channel (bounded by a
   * server-side cap). Android only.
   *
   * The script rides the first frame; the channel sends it as soon as it opens.
   */
  stream(script: string, process: string, timeout = 0): Channel<unknown> {
    const url = channelUrl(this.cfg, this.uuid, "frida/stream", {
      process,
      timeout: String(timeout),
    });
    const ch = new Channel(url, decodeJson);
    void ch.send(script); // send() awaits ch.ready internally
    return ch;
  }
}

/**
 * `sandbox.debugger` — the on-device lldb (lldb-server + attach).
 *
 * status/install/start go through `POST /sandboxes/<uuid>/debugger` (gated like
 * the shell); `console` opens the interactive lldb stream. Needs a rootable
 * image for ptrace, so on Cuttlefish use a debug sandbox.
 */
export class Debugger {
  private readonly base: string;
  constructor(
    private readonly http: Http,
    private readonly cfg: ResolvedConfig,
    private readonly uuid: string,
  ) {
    this.base = `/sandboxes/${uuid}/debugger`;
  }

  /** Report lldb-server state (installed/running/port). */
  status(): Promise<unknown> {
    return this.http.get(this.base);
  }

  /** Push lldb-server to the device (needs root) and start it. */
  install(): Promise<unknown> {
    return this.http.post(this.base, { action: "install" });
  }

  /** Start lldb-server, optionally attaching it to `process`. */
  start(process?: string): Promise<unknown> {
    return this.http.post(this.base, { action: "start", process });
  }

  /** Interactive lldb console stream (send commands with `.send()`). */
  console(process?: string): Channel<string> {
    return new Channel(
      channelUrl(this.cfg, this.uuid, "debugger/console", { process }),
      decodeText,
    );
  }
}

/** `sandbox.snapshots` — point-in-time snapshots of this sandbox. */
export class SandboxSnapshots {
  private readonly base: string;
  constructor(
    private readonly http: Http,
    uuid: string,
  ) {
    this.base = `/sandboxes/${uuid}`;
  }

  list(): Promise<SnapshotRow[]> {
    return this.http.get<SnapshotRow[]>(`${this.base}/snapshots`);
  }

  create(name: string): Promise<unknown> {
    return this.http.post(`${this.base}/snapshots`, { name });
  }

  restore(name: string): Promise<unknown> {
    return this.http.post(`${this.base}/snapshots/${name}`);
  }

  delete(name: string): Promise<unknown> {
    return this.http.del(`${this.base}/snapshots/${name}`);
  }

  saveAsTemplate(opts: {
    name: string;
    visibility?: "private" | "org";
    description?: string;
    snapshot?: string;
  }): Promise<SnapshotRow> {
    return this.http.post<SnapshotRow>(`${this.base}/template`, {
      visibility: "private",
      description: "",
      ...opts,
    });
  }
}

export type { ApiKey }; // re-export for convenience
