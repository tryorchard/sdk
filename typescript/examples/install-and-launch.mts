// Install an APK, launch it and save a screenshot.
// Usage: node --experimental-strip-types examples/install-and-launch.mts <selector> <app.apk> <package>
import { readFile, writeFile } from "node:fs/promises";
import { basename } from "node:path";
import { setTimeout as sleep } from "node:timers/promises";

import { Orchard } from "@orchard/sdk";

const [selector, apk, pkg] = process.argv.slice(2);
if (!pkg) throw new Error("usage: install-and-launch.mts <selector> <app.apk> <package>");

const orchard = Orchard.fromEnv();
const sb = await orchard.sandbox(selector);
if ((await sb.get()).state !== "running") await sb.start();

await sb.apps.install(new File([await readFile(apk)], basename(apk)));
await sb.launch(pkg);
await sleep(3000);

await writeFile("screenshot.png", await sb.screenshot());
console.log(`installed ${pkg} and saved screenshot.png`);
