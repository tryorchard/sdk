/**
 * Orchard SDK — a TypeScript/JavaScript client for the Orchard mobile-sandbox
 * control plane. Works in Node (≥18) and the browser.
 *
 * ```ts
 * import { Orchard } from "@tryorchard/sdk";
 * const orchard = Orchard.fromEnv();            // ORCHARD_API_URL + ORCHARD_API_KEY
 * for (const s of (await orchard.sandboxes.list()).instances) console.log(s.name, s.state);
 * ```
 * @packageDocumentation
 */
export { Orchard } from "./client.js";
export type { OrchardOptions, ResolvedConfig } from "./config.js";
export { ApiError, ChannelClosedError, OrchardError, SelectorError } from "./errors.js";
export { Channel } from "./ws.js";
export { resolve, resolveAll } from "./selector.js";
export type {
  ApiKey,
  Capability,
  FlowEvent,
  Instance,
  InstanceList,
  Job,
  LogLine,
  Platform,
  Provider,
  SnapshotRow,
} from "./models.js";
export { Sandbox, Sandboxes, Files, Apps, Frida, Debugger, SandboxSnapshots } from "./resources/sandboxes.js";
export { Keys, Snapshots, Templates, Catalog, Jobs, Nodes, Team, Workspaces, Remote } from "./resources/index.js";
export type { Uploadable } from "./resources/sandboxes.js";
