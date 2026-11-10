// Mint a 30-day key that can only read logs and files of one sandbox.
// Usage: node --experimental-strip-types examples/scoped-key.mts <selector>
import { Orchard } from "@tryorchard/sdk";

const [selector] = process.argv.slice(2);
if (!selector) throw new Error("usage: scoped-key.mts <selector>");

const orchard = Orchard.fromEnv();
const sb = await orchard.sandbox(selector);
const key = await orchard.keys.create("ci-logs-only", {
  sandboxUuids: [sb.uuid],
  allowedFeatures: ["logs", "files"],
  expiresInDays: 30,
});
console.log("new scoped key (shown once):", key.token);
