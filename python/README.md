# orchardsdk

Python client for [Orchard](https://docs.orchard.airoverflow.com): create and drive iOS and Android sandboxes, manage snapshots, templates, teams and scoped API keys, and stream live channels (logs, shell, screen, adb, VNC, mitm, frida).

```bash
pip install orchardsdk
```

Requires Python 3.10+. The import name is `orchard_sdk`.

## Quickstart

```python
from orchard_sdk import Orchard

orchard = Orchard.from_env()  # ORCHARD_API_URL + ORCHARD_API_KEY
# or: Orchard("https://orchard.example.com", "orc_live_xxx")

for s in orchard.sandboxes.list()["instances"]:
    print(s["name"], s["state"])

sb = orchard.sandbox("my-pixel")  # uuid, uuid prefix, name or tag
sb.start()
sb.apps.install("./build/app.apk")
sb.launch("com.example.app")
sb.tap_text("Sign in")

with open("screen.png", "wb") as f:
    f.write(sb.screenshot())

with sb.logs() as stream:
    for line in stream:
        print(line)
```

## Configuration

| Variable | Purpose |
| --- | --- |
| `ORCHARD_API_URL` | Control-plane URL, e.g. `https://orchard.example.com` |
| `ORCHARD_API_KEY` | API key (`orc_…`) or JWT access token |
| `ORCHARD_ORG` | Optional org slug (ignored for API keys) |
| `ORCHARD_WS` | Optional workspace slug |

Explicit arguments to `Orchard(...)` win over the environment. The client holds a connection pool: use it as a context manager or call `close()`.

## Live channels

Channels are context-managed iterators that work in ordinary synchronous code:

```python
with sb.shell() as sh:
    sh.send("getprop ro.build.version.release\n")
    for out in sh:
        print(out, end="")
```

For asyncio code use `orchard_sdk.aio.AsyncChannels`:

```python
import asyncio
from orchard_sdk import from_env
from orchard_sdk.aio import AsyncChannels

async def main():
    async for line in AsyncChannels(from_env(), sb.uuid).logs():
        print(line)

asyncio.run(main())
```

Expose a device channel on a local port for ordinary tools:

```python
with sb.adb_bridge() as bridge:
    print(f"adb connect 127.0.0.1:{bridge.port}")
```

## Errors

All errors derive from `OrchardError`: `ApiError` (HTTP status + server detail), `SelectorError` (zero or ambiguous sandbox match), `ChannelClosedError` (WebSocket closed with 4401/4403/4404/4502).

```python
from orchard_sdk import ApiError, SelectorError

try:
    orchard.sandbox("pixel").start()
except SelectorError as e:
    print(e)
except ApiError as e:
    print(e.status, e.detail)
```

## Documentation

- [API reference](https://github.com/tryorchard/sdk/blob/main/python/docs/reference.md): every method, with examples
- [Examples](https://github.com/tryorchard/sdk/tree/main/python/examples): install and launch, UI test with snapshot rollback, frida tracing, traffic capture, adb bridge, scoped keys, log streaming

## License

MIT
