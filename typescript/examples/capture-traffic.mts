// Save the mitm CA and print HTTP(S) flows as the app makes them.
// Start capture for the sandbox in the Orchard console first.
// Usage: node --experimental-strip-types examples/capture-traffic.mts <selector>
import { writeFile } from "node:fs/promises";

import { Orchard } from "@orchard/sdk";

const [selector] = process.argv.slice(2);
if (!selector) throw new Error("usage: capture-traffic.mts <selector>");

const orchard = Orchard.fromEnv();
const sb = await orchard.sandbox(selector);
await writeFile("orchard-mitm-ca.pem", await sb.mitmCa());

type Flow = { method: string; status: number | null; scheme: string; host: string; path: string };
for await (const flow of sb.mitmFlows()) {
  const f = flow as Flow;
  console.log(f.method, f.status, `${f.scheme}://${f.host}${f.path}`);
}
