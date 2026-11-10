// Drive a login screen, then roll the sandbox back to a clean snapshot.
// Usage: node --experimental-strip-types examples/ui-test.mts <selector> <package>
import { writeFile } from "node:fs/promises";
import { setTimeout as sleep } from "node:timers/promises";

import { Orchard } from "@tryorchard/sdk";

const [selector, pkg] = process.argv.slice(2);
if (!pkg) throw new Error("usage: ui-test.mts <selector> <package>");

const orchard = Orchard.fromEnv();
const sb = await orchard.sandbox(selector);

await sb.snapshots.create("before-ui-test");
try {
  await sb.launch(pkg);
  await sleep(2000);
  await sb.tapText("Email");
  await sb.text("demo@example.com");
  await sb.tapText("Password");
  await sb.text("hunter2");
  await sb.tapText("Sign in");
  await sleep(2000);

  const labels = JSON.stringify(await sb.describeUi());
  console.log(labels.includes("Welcome") ? "PASS" : "FAIL: no welcome screen");
  await writeFile("after-login.png", await sb.screenshot());
} finally {
  await sb.snapshots.restore("before-ui-test");
  await sb.snapshots.delete("before-ui-test");
}
