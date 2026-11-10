// List sandboxes. Usage: node --experimental-strip-types examples/quickstart.mts
import { Orchard } from "@tryorchard/sdk";

const orchard = Orchard.fromEnv();

const me = await orchard.me();
console.log("authenticated as", me.username);

const { instances } = await orchard.sandboxes.list();
for (const s of instances) console.log(`  ${s.name}\t${s.state}\ttag=${s.tag || "-"}`);
