/** The Orchard client facade. @packageDocumentation */
import { type OrchardOptions, type ResolvedConfig, resolveConfig } from "./config.js";
import { Http } from "./http.js";
import { Catalog, Jobs, Keys, Nodes, Remote, Snapshots, Team, Templates, Workspaces } from "./resources/index.js";
import { Sandbox, Sandboxes } from "./resources/sandboxes.js";

/**
 * A client for an Orchard control plane.
 *
 * ```ts
 * import { Orchard } from "@orchard/sdk";
 *
 * const orchard = new Orchard({ url: "https://orchard.example.com", token: "orc_…" });
 * const { instances } = await orchard.sandboxes.list();
 * const sb = await orchard.sandbox("my-pixel");   // uuid / prefix / name / tag
 * await sb.tag("payments", "#22c55e");
 * for await (const line of sb.logs()) console.log(line);
 * ```
 */
export class Orchard {
  /** The resolved connection config. */
  readonly config: ResolvedConfig;
  /** Fleet-wide sandbox listing and creation. */
  readonly sandboxes: Sandboxes;
  /** Point-in-time snapshots across the org. */
  readonly snapshots: Snapshots;
  /** Reusable sandbox templates. */
  readonly templates: Templates;
  /** API keys (including fine-grained scoped keys). */
  readonly keys: Keys;
  /** The organization, its members and invites. */
  readonly team: Team;
  /** Workspaces (teams) within the org. */
  readonly workspaces: Workspaces;
  /** What can be launched (images, presets, device types). */
  readonly catalog: Catalog;
  /** Background jobs. */
  readonly jobs: Jobs;
  /** Infrastructure nodes. */
  readonly nodes: Nodes;
  /** Remote (cloud) sandboxes and credentials. */
  readonly remote: Remote;

  private readonly http: Http;

  constructor(opts: OrchardOptions = {}) {
    this.config = resolveConfig(opts);
    this.http = new Http(this.config);
    this.sandboxes = new Sandboxes(this.http, this.config);
    this.snapshots = new Snapshots(this.http);
    this.templates = new Templates(this.http);
    this.keys = new Keys(this.http);
    this.team = new Team(this.http);
    this.workspaces = new Workspaces(this.http);
    this.catalog = new Catalog(this.http);
    this.jobs = new Jobs(this.http, this.config);
    this.nodes = new Nodes(this.http);
    this.remote = new Remote(this.http, this.config);
  }

  /** Build a client from the `ORCHARD_*` environment variables (Node). */
  static fromEnv(): Orchard {
    return new Orchard();
  }

  /** The authenticated identity: orgs, active org/workspace, features. */
  me(): Promise<Record<string, unknown>> {
    return this.http.get("/me");
  }

  /** Resolve a selector (uuid / uuid-prefix / name / tag) to a {@link Sandbox}. */
  async sandbox(selector: string): Promise<Sandbox> {
    const inst = await this.sandboxes.resolve(selector);
    return this.sandboxes.get(inst.uuid as string);
  }
}
