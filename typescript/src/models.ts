/**
 * Typed shapes for Orchard's wire JSON. The control plane is the source of
 * truth, so these are intentionally permissive (optional fields marked `?`).
 * @packageDocumentation
 */

export type Platform = "ios" | "android";
export type Provider =
  | "vphone" | "baguette" | "android" | "cuttlefish" | "qemu"
  | "e2b" | "daytona" | "modal";

/** One capability of a sandbox and whether the caller may use it. */
export interface Capability {
  key: string;
  supported: boolean;
  available: boolean;
  reason: string;
}

/** A sandbox, as returned by `GET /api/instances` and `/api/sandboxes/<uuid>`. */
export interface Instance {
  id: string;
  /** Stable external id; `null` for unmanaged sandboxes. */
  uuid?: string | null;
  provider: Provider;
  platform: Platform;
  location?: "node" | "remote";
  /** Remote-only: the `/api/remote/<id>` lifecycle key. */
  record_id?: number;
  external_id?: string;
  key: string;
  name: string;
  display_name: string;
  node: string | null;
  node_id?: number;
  state: string;
  variant: string;
  os_version: string | null;
  os_build: string | null;
  mode: string;
  mode_label: string;
  owner: string | null;
  notes?: string;
  /** User-chosen label + chip colour ("#rrggbb" or ""). */
  tag?: string;
  tag_color?: string;
  read_only: boolean;
  unmanaged?: boolean;
  can_manage?: boolean;
  image?: string;
  image_installed?: boolean;
  family?: string | null;
  device?: string | null;
  files_home?: string;
  buttons?: string[];
  capabilities: Record<string, Capability>;
  hardware: {
    cpu: number | null;
    memory_mb: number | null;
    disk_bytes: number | null;
    udid: string | null;
    screen_points?: { width: number; height: number };
  };
  runtime: {
    state: string;
    pid: number | null;
    adopted: boolean;
    guest_ip: string | null;
    guest_os?: string | null;
    uptime_s: number | null;
    log_lines: number;
    serial?: string | null;
    error?: string | null;
  };
  vnc?: { port: number; password: string };
  screen?: { width: number | null; height: number | null; ppi: number | null; scale: number | null };
  expires_at?: string | null;
  auto_action?: string;
}

/** The `GET /api/instances` envelope. */
export interface InstanceList {
  instances: Instance[];
  errors: { node: string; detail: string }[];
}

/**
 * Android kernel-modularity options for {@link Sandboxes.create} /
 * {@link Templates.launch}. All optional; they merge into the create body.
 *
 * `kernel`/`ramdisk` name files in the node kernel store (see {@link Nodes});
 * `kernel_cmdline` is extra boot cmdline; `boot_props` are guest `ro.*`/`persist.*`
 * props; `kernel_gdb` boots with a halted gdb stub (bridge with {@link Sandbox.gdb}).
 */
export interface KernelOptions {
  rooted?: boolean;
  kernel_gdb?: boolean;
  kernel?: string;
  ramdisk?: string;
  kernel_cmdline?: string;
  boot_props?: Record<string, string>;
  device_profile?: string;
  isolated?: boolean;
}

/** A kernel/ramdisk/vmlinux file in a node's kernel store. */
export interface KernelFile {
  name: string;
  size: number;
}

/** A point-in-time snapshot or a template row. */
export interface SnapshotRow {
  id: number;
  uuid: string;
  name: string;
  kind: "point" | "template";
  node: string;
  provider: string;
  platform: Platform;
  instance_key: string;
  instance_uuid: string | null;
  template_id: string;
  visibility: "private" | "org";
  description: string;
  created_by: string | null;
  created_at: string;
  meta: Record<string, unknown>;
}

/** A session recording's metadata (`meta.json`): a screen video plus a
 * replayable input-action log. */
export interface Recording {
  id: string;
  kind: string;
  key: string;
  status: "recording" | "done";
  /** Unix epoch seconds when recording started. */
  started: number;
  /** Seconds captured so far. */
  duration: number;
  /** Number of logged input actions. */
  actions: number;
  video: boolean;
  video_bytes: number;
}

/** One timestamped input event in a recording's action log (`t` is seconds
 * since the recording started). */
export type RecordedAction = { t: number } & (
  | { tap: [number, number] }
  | { swipe: number[]; ms: number }
  | { text: string }
  | { key: string }
);

/** A background job (image download, vm create). */
export interface Job {
  id: string;
  node: string;
  kind: string;
  target: string;
  state: string;
  phase?: string;
  progress?: number | null;
  exit_code: number | null;
  started_at: number;
  finished_at: number | null;
  elapsed_s: number;
}

/** An API key row. The raw `token` is only present in the create response. */
export interface ApiKey {
  id: number;
  name: string;
  hint: string;
  token?: string;
  created_at: string;
  expires_at: string | null;
  last_used: string | null;
  sandbox_uuids?: string[];
  tag?: string;
  allowed_features?: string[] | null;
}

/** A single log frame from the `logs` channel. */
export interface LogLine {
  ts?: number;
  source?: string;
  text: string;
}

/** A captured HTTP(S) flow summary from the `mitm/flows` channel. */
export type FlowEvent = Record<string, unknown>;
