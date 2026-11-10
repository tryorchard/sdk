# @tryorchard/sdk

TypeScript/JavaScript client for [Orchard](https://docs.orchard.airoverflow.com): create and drive iOS and Android sandboxes, manage snapshots, templates, teams and scoped API keys, and stream live channels (logs, shell, screen, adb, VNC, mitm, frida). Ships ESM, CommonJS and type declarations; runs in Node 18+ and the browser.

```bash
npm i @tryorchard/sdk
```

On Node < 21 (no global `WebSocket`) also install the optional peer for live channels: `npm i ws`.

## Quickstart

```ts
import { readFile, writeFile } from "node:fs/promises";
import { Orchard } from "@tryorchard/sdk";

const orchard = Orchard.fromEnv(); // ORCHARD_API_URL + ORCHARD_API_KEY
// or: new Orchard({ url: "https://orchard.example.com", token: "orc_live_xxx" })

const { instances } = await orchard.sandboxes.list();
for (const s of instances) console.log(s.name, s.state);

const sb = await orchard.sandbox("my-pixel"); // uuid, uuid prefix, name or tag
await sb.start();
await sb.apps.install(new File([await readFile("./build/app.apk")], "app.apk"));
await sb.launch("com.example.app");
await sb.tapText("Sign in");

await writeFile("screen.png", await sb.screenshot());

for await (const line of sb.logs()) console.log(line);
```

CommonJS works too: `const { Orchard } = require("@tryorchard/sdk")`.

## Configuration

| Option | Variable | Purpose |
| --- | --- | --- |
| `url` | `ORCHARD_API_URL` | Control-plane URL, e.g. `https://orchard.example.com` |
| `token` | `ORCHARD_API_KEY` | API key (`orc_…`) or JWT access token |
| `org` | `ORCHARD_ORG` | Optional org slug (ignored for API keys) |
| `ws` | `ORCHARD_WS` | Optional workspace slug |
| `timeout` | | REST timeout in ms (default 60000) |

Options passed to `new Orchard({...})` win over the environment.

## Live channels

Every stream is a `Channel<T>`: iterate it with `for await`, or listen with `.on()`, push data with `.send()`, stop with `.close()`.

```ts
const sh = sb.shell();
sh.on("message", (out) => process.stdout.write(String(out)));
await sh.send("getprop ro.build.version.release\n");
setTimeout(() => sh.close(), 5000);
```

## Browser

The same package works with the browser's `fetch` and `WebSocket`. An `orc_` key is a bearer credential: ship it only to trusted frontends, or proxy through your backend.

## Errors

All errors extend `OrchardError`: `ApiError` (HTTP status + server detail), `SelectorError` (zero or ambiguous sandbox match), `ChannelClosedError` (WebSocket closed with 4401/4403/4404/4502).

```ts
import { ApiError, SelectorError } from "@tryorchard/sdk";

try {
  await (await orchard.sandbox("pixel")).start();
} catch (e) {
  if (e instanceof SelectorError) console.error(e.message);
  else if (e instanceof ApiError) console.error(e.status, e.detail);
  else throw e;
}
```

## Documentation

- [API reference](https://github.com/tryorchard/sdk/blob/main/typescript/docs/reference.md): every method, with examples
- [Examples](https://github.com/tryorchard/sdk/tree/main/typescript/examples): install and launch, UI test with snapshot rollback, frida tracing, traffic capture, scoped keys, log streaming

## License

MIT
