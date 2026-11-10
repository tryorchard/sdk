/** Smaller resource namespaces: keys, snapshots, templates, catalog, jobs, nodes,
 * team, workspaces, remote. @packageDocumentation */
import type { ResolvedConfig } from "../config.js";
import type { Http } from "../http.js";
import type { ApiKey, Job, SnapshotRow } from "../models.js";
import { Channel, decodeText, rawChannelUrl } from "../ws.js";

export { Sandboxes, Sandbox, Files, Apps, Frida, Debugger, SandboxSnapshots } from "./sandboxes.js";

/** `orchard.keys` — API keys, including fine-grained scoped keys. */
export class Keys {
  constructor(private readonly http: Http) {}

  list(): Promise<ApiKey[]> {
    return this.http.get<ApiKey[]>("/tokens");
  }

  /**
   * Mint an API key; the raw secret is in the response `token` (shown once).
   * Scope it with `sandboxUuids` (specific sandboxes), `tag` (all sandboxes with
   * that tag, now and future) and `allowedFeatures` (a capability subset).
   */
  create(
    name: string,
    opts: {
      sandboxUuids?: string[];
      tag?: string;
      allowedFeatures?: string[];
      expiresInDays?: number;
    } = {},
  ): Promise<ApiKey> {
    const body: Record<string, unknown> = { name };
    if (opts.expiresInDays !== undefined) body.expires_in_days = opts.expiresInDays;
    if (opts.sandboxUuids !== undefined) body.sandbox_uuids = opts.sandboxUuids;
    if (opts.tag !== undefined) body.tag = opts.tag;
    if (opts.allowedFeatures !== undefined) body.capabilities = opts.allowedFeatures;
    return this.http.post<ApiKey>("/tokens", body);
  }

  delete(id: number): Promise<unknown> {
    return this.http.del(`/tokens/${id}`);
  }
}

/** `orchard.snapshots` — every point snapshot in the org/workspace. */
export class Snapshots {
  constructor(private readonly http: Http) {}
  list(): Promise<SnapshotRow[]> {
    return this.http.get<SnapshotRow[]>("/snapshots");
  }
}

/** `orchard.templates` — reusable sandbox templates. */
export class Templates {
  constructor(private readonly http: Http) {}
  list(): Promise<SnapshotRow[]> {
    return this.http.get<SnapshotRow[]>("/templates");
  }
  delete(pk: number): Promise<unknown> {
    return this.http.del(`/templates/${pk}`);
  }
  launch(pk: number, name: string, spec: Record<string, unknown> = {}): Promise<unknown> {
    return this.http.post(`/templates/${pk}/launch`, { name, ...spec });
  }
}

/** `orchard.catalog` — what can be launched. */
export class Catalog {
  constructor(private readonly http: Http) {}
  android(): Promise<unknown> {
    return this.http.get("/android/catalog");
  }
  presets(): Promise<unknown> {
    return this.http.get("/presets");
  }
  simDeviceTypes(): Promise<unknown> {
    return this.http.get("/sim/device-types");
  }
  providers(): Promise<unknown> {
    return this.http.get("/providers");
  }
}

/** `orchard.jobs` — background jobs. */
export class Jobs {
  constructor(
    private readonly http: Http,
    private readonly cfg: ResolvedConfig,
  ) {}
  list(): Promise<Job[]> {
    return this.http.get<Job[]>("/jobs");
  }
  cancel(node: string, jobId: string): Promise<unknown> {
    return this.http.post(`/jobs/${node}/${jobId}/cancel`);
  }
  /** Stream a job's log lines. */
  logs(node: string, kind: string, name: string): Channel<string> {
    return new Channel(rawChannelUrl(this.cfg, `ws/jobs/${node}/${kind}/${name}/logs`), decodeText);
  }
}

/** `orchard.nodes` — infrastructure nodes (mostly platform-admin). */
export class Nodes {
  constructor(private readonly http: Http) {}
  list(): Promise<unknown[]> {
    return this.http.get<unknown[]>("/nodes");
  }
  create(cfg: Record<string, unknown>): Promise<unknown> {
    return this.http.post("/nodes", cfg);
  }
  test(cfg: Record<string, unknown>): Promise<unknown> {
    return this.http.post("/nodes/test", cfg);
  }
  refresh(pk: number): Promise<unknown> {
    return this.http.post(`/nodes/${pk}/refresh`);
  }
  delete(pk: number): Promise<unknown> {
    return this.http.del(`/nodes/${pk}`);
  }
}

class Members {
  constructor(
    private readonly http: Http,
    private readonly base: string,
  ) {}
  list(): Promise<unknown[]> {
    return this.http.get<unknown[]>(`${this.base}/members`);
  }
  edit(pk: number, fields: Record<string, unknown>): Promise<unknown> {
    return this.http.patch(`${this.base}/members/${pk}`, fields);
  }
  remove(pk: number): Promise<unknown> {
    return this.http.del(`${this.base}/members/${pk}`);
  }
}

class Invites {
  constructor(
    private readonly http: Http,
    private readonly base: string,
  ) {}
  list(): Promise<unknown[]> {
    return this.http.get<unknown[]>(`${this.base}/invites`);
  }
  create(role = "member"): Promise<{ token: string; expires_at: string }> {
    return this.http.post(`${this.base}/invites`, { role });
  }
  delete(pk: number): Promise<unknown> {
    return this.http.del(`${this.base}/invites/${pk}`);
  }
}

/** `orchard.team` — the active organization, its members and invites. */
export class Team {
  readonly members: Members;
  readonly invites: Invites;
  constructor(private readonly http: Http) {
    this.members = new Members(http, "/org");
    this.invites = new Invites(http, "/org");
  }
  get(): Promise<unknown> {
    return this.http.get("/org");
  }
  edit(fields: Record<string, unknown>): Promise<unknown> {
    return this.http.patch("/org", fields);
  }
  inviteInfo(token: string): Promise<unknown> {
    return this.http.get(`/invites/${token}`);
  }
  acceptInvite(token: string, account: Record<string, unknown> = {}): Promise<unknown> {
    return this.http.post(`/invites/${token}`, account);
  }
}

class Workspace {
  readonly members: Members;
  readonly invites: Invites;
  constructor(
    private readonly http: Http,
    readonly slug: string,
  ) {
    this.members = new Members(http, `/workspaces/${slug}`);
    this.invites = new Invites(http, `/workspaces/${slug}`);
  }
  edit(fields: Record<string, unknown>): Promise<unknown> {
    return this.http.patch(`/workspaces/${this.slug}`, fields);
  }
  delete(): Promise<unknown> {
    return this.http.del(`/workspaces/${this.slug}`);
  }
}

/** `orchard.workspaces` — teams within the org. */
export class Workspaces {
  constructor(private readonly http: Http) {}
  async list(): Promise<unknown[]> {
    const me = await this.http.get<{ workspaces?: unknown[] }>("/me");
    return me.workspaces ?? [];
  }
  create(name: string, slug?: string): Promise<unknown> {
    return this.http.post("/workspaces", slug ? { name, slug } : { name });
  }
  get(slug: string): Workspace {
    return new Workspace(this.http, slug);
  }
}

/** `orchard.remote` — cloud sandboxes and provider credentials. */
export class Remote {
  constructor(
    private readonly http: Http,
    private readonly cfg: ResolvedConfig,
  ) {}
  credentials(): Promise<unknown[]> {
    return this.http.get<unknown[]>("/credentials");
  }
  addCredential(provider: string, key: string, extra: Record<string, unknown> = {}): Promise<unknown> {
    return this.http.post("/credentials", { provider, key, ...extra });
  }
  deleteCredential(pk: number): Promise<unknown> {
    return this.http.del(`/credentials/${pk}`);
  }
  catalog(): Promise<unknown> {
    return this.http.get("/remote/catalog");
  }
  create(provider: string, name: string, spec: Record<string, unknown> = {}): Promise<unknown> {
    return this.http.post("/remote/create", { provider, name, ...spec });
  }
  get(ref: number | string): Promise<unknown> {
    return this.http.get(`/remote/${ref}`);
  }
  delete(ref: number | string): Promise<unknown> {
    return this.http.del(`/remote/${ref}`);
  }
  start(ref: number | string): Promise<unknown> {
    return this.http.post(`/remote/${ref}/start`);
  }
  stop(ref: number | string): Promise<unknown> {
    return this.http.post(`/remote/${ref}/stop`);
  }
  /** An interactive shell to a remote sandbox. */
  shell(ref: number | string): Channel<string> {
    return new Channel(rawChannelUrl(this.cfg, `ws/remote/${ref}/shell`), decodeText);
  }
  /** Upload a file into a remote sandbox (bytes, or a browser File/Blob). */
  upload(ref: number | string, data: Uint8Array | Blob, path?: string, filename = "upload"): Promise<unknown> {
    const form = new FormData();
    form.append("file", data instanceof Blob ? data : new Blob([data as BlobPart]), filename);
    if (path) form.append("path", path);
    return this.http.postForm(`/remote/${ref}/files`, form);
  }
  /** Download a file from a remote sandbox; resolves to its bytes. */
  download(ref: number | string, path: string): Promise<Uint8Array> {
    return this.http.getBytes(`/remote/${ref}/files/download?path=${encodeURIComponent(path)}`);
  }
  /** Stream a remote sandbox's logs. */
  logs(ref: number | string): Channel<string> {
    return new Channel(rawChannelUrl(this.cfg, `ws/remote/${ref}/logs`), decodeText);
  }
  /** Live resource sample (cpu/mem/uptime, sampled inside the sandbox). */
  metrics(ref: number | string): Promise<unknown> {
    return this.http.get(`/remote/${ref}/metrics`);
  }
}
