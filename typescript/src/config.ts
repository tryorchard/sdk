/** Connection configuration. @packageDocumentation */

export interface OrchardOptions {
  /** Control-plane base URL, e.g. `https://orchard.example.com`. */
  url?: string;
  /** API key (`orc_…`) or JWT access token. */
  token?: string;
  /** Organization slug (`X-Orchard-Org`). Ignored for API keys. */
  org?: string;
  /** Workspace slug (`X-Orchard-Workspace`). */
  ws?: string;
  /** REST request timeout in milliseconds (default 60000). */
  timeout?: number;
}

export interface ResolvedConfig {
  url: string;
  token: string;
  org?: string;
  ws?: string;
  timeout: number;
}

/** REST base, e.g. `https://host/api`. */
export function apiBase(cfg: ResolvedConfig): string {
  return cfg.url.replace(/\/+$/, "") + "/api";
}

/** WebSocket origin, e.g. `wss://host` (path/query of `url` dropped). */
export function wsBase(cfg: ResolvedConfig): string {
  const u = new URL(cfg.url);
  const scheme = u.protocol === "https:" ? "wss" : "ws";
  return `${scheme}://${u.host}`;
}

/** Resolve options against `process.env` (Node), letting options win. */
export function resolveConfig(opts: OrchardOptions = {}): ResolvedConfig {
  const env = typeof process !== "undefined" ? process.env : ({} as Record<string, string>);
  const url = opts.url ?? env.ORCHARD_API_URL ?? env.ORCHARD_URL;
  const token = opts.token ?? env.ORCHARD_API_KEY;
  if (!url) throw new Error("no Orchard URL: pass url or set ORCHARD_API_URL");
  if (!token) throw new Error("no Orchard token: pass token or set ORCHARD_API_KEY");
  return {
    url,
    token,
    org: opts.org ?? env.ORCHARD_ORG,
    ws: opts.ws ?? env.ORCHARD_WS,
    timeout: opts.timeout ?? 60000,
  };
}
