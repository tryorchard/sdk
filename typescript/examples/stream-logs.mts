// Stream a sandbox's logs. Usage: node --experimental-strip-types examples/stream-logs.mts <selector>
import { Orchard } from "@orchard/sdk";

const [selector] = process.argv.slice(2);
if (!selector) throw new Error("usage: stream-logs.mts <selector>");

const orchard = Orchard.fromEnv();
const sb = await orchard.sandbox(selector);
console.log(`streaming logs from ${selector} (${sb.uuid.slice(0, 8)}), Ctrl-C to stop`);

for await (const line of sb.logs()) console.log(line);
