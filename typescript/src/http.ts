/** The REST transport: a `fetch` wrapper that knows Orchard's base URL, auth and
 * error mapping. Internal — use {@link Orchard}. @packageDocumentation */
import { apiBase, type ResolvedConfig } from "./config.js";
import { ApiError } from "./errors.js";

async function detail(resp: Response): Promise<string> {
  const text = await resp.text();
  try {
    const body = JSON.parse(text);
    if (body && typeof body === "object") return String(body.detail ?? text);
  } catch {
    /* not JSON */
  }
  return text.slice(0, 300).trim();
}

export interface ReqOpts {
  query?: Record<string, string | undefined>;
  json?: unknown;
  form?: FormData;
}

/** Thin, typed wrapper over global `fetch`, scoped to one org/workspace. */
export class Http {
  private readonly base: string;
  private readonly headers: Record<string, string>;

  constructor(private readonly cfg: ResolvedConfig) {
    this.base = apiBase(cfg);
    this.headers = { Authorization: `Bearer ${cfg.token}` };
    if (cfg.org) this.headers["X-Orchard-Org"] = cfg.org;
    if (cfg.ws) this.headers["X-Orchard-Workspace"] = cfg.ws;
  }

  private url(path: string, query?: ReqOpts["query"]): string {
    const u = new URL(this.base + path);
    for (const [k, v] of Object.entries(query ?? {})) if (v !== undefined) u.searchParams.set(k, v);
    return u.toString();
  }

  private async send(method: string, path: string, opts: ReqOpts = {}): Promise<Response> {
    const headers = { ...this.headers };
    let body: BodyInit | undefined;
    if (opts.json !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(opts.json);
    } else if (opts.form) {
      body = opts.form; // browser/Node set the multipart boundary automatically
    }
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), this.cfg.timeout);
    let resp: Response;
    try {
      resp = await fetch(this.url(path, opts.query), { method, headers, body, signal: ctrl.signal });
    } finally {
      clearTimeout(timer);
    }
    if (resp.status >= 400) throw new ApiError(resp.status, await detail(resp));
    return resp;
  }

  private async json<T>(method: string, path: string, opts?: ReqOpts): Promise<T> {
    const resp = await this.send(method, path, opts);
    if (resp.status === 204) return undefined as T;
    const text = await resp.text();
    return (text ? JSON.parse(text) : undefined) as T;
  }

  get<T>(path: string, query?: ReqOpts["query"]): Promise<T> {
    return this.json<T>("GET", path, { query });
  }

  async getBytes(path: string): Promise<Uint8Array> {
    const resp = await this.send("GET", path);
    return new Uint8Array(await resp.arrayBuffer());
  }

  post<T>(path: string, json?: unknown): Promise<T> {
    return this.json<T>("POST", path, { json });
  }

  postForm<T>(path: string, form: FormData): Promise<T> {
    return this.json<T>("POST", path, { form });
  }

  patch<T>(path: string, json?: unknown): Promise<T> {
    return this.json<T>("PATCH", path, { json });
  }

  del<T>(path: string): Promise<T> {
    return this.json<T>("DELETE", path);
  }

  /** The control-plane origin + path, for building signed-grant download URLs. */
  absolute(path: string): string {
    return this.cfg.url.replace(/\/+$/, "") + path;
  }

  /** GET a signed-grant URL (token in the URL) with no auth header → bytes. */
  async download(absoluteUrl: string): Promise<Uint8Array> {
    const resp = await fetch(absoluteUrl);
    if (resp.status >= 400) throw new ApiError(resp.status, await detail(resp));
    return new Uint8Array(await resp.arrayBuffer());
  }
}
