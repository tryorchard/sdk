// Stream Activity.onResume calls from an Android app with frida.
// Usage: node --experimental-strip-types examples/frida-trace.mts <selector> <package>
import { Orchard } from "@tryorchard/sdk";

const [selector, pkg] = process.argv.slice(2);
if (!pkg) throw new Error("usage: frida-trace.mts <selector> <package>");

const script = `
Java.perform(() => {
  const Activity = Java.use("android.app.Activity");
  Activity.onResume.implementation = function () {
    send("onResume " + this.getClass().getName());
    this.onResume();
  };
});
`;

const orchard = Orchard.fromEnv();
const sb = await orchard.sandbox(selector);

const status = (await sb.frida.status()) as { installed?: boolean; running?: boolean };
if (!status.installed) await sb.frida.install();
else if (!status.running) await sb.frida.start();

await sb.launch(pkg);
for await (const msg of sb.frida.stream(script, pkg, 60)) console.log(msg);
