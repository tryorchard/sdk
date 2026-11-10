# Orchard SDKs

Official clients for the [Orchard](https://docs.orchard.airoverflow.com) mobile-sandbox control plane.

| Language | Package | Install | Docs |
| --- | --- | --- | --- |
| Python 3.10+ | [`orchardsdk`](python) | `pip install orchardsdk` | [reference](python/docs/reference.md), [examples](python/examples) |
| TypeScript / JavaScript | [`@orchard/sdk`](typescript) | `npm i @orchard/sdk` | [reference](typescript/docs/reference.md), [examples](typescript/examples) |

Both read `ORCHARD_API_URL` and `ORCHARD_API_KEY` from the environment and expose the same surface (snake_case in Python, camelCase in TypeScript).

```python
from orchard_sdk import Orchard

sb = Orchard.from_env().sandbox("my-pixel")
sb.tap_text("Sign in")
```

```ts
import { Orchard } from "@orchard/sdk";

const sb = await Orchard.fromEnv().sandbox("my-pixel");
await sb.tapText("Sign in");
```

## License

[MIT](LICENSE)
