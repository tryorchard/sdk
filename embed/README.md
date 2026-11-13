# Embedding Orchard devices

Put a **live Orchard device** — its screen, and optionally taps/keys — inside your
own web app, so your users can watch and drive sandboxes without ever leaving your
UI and without ever seeing your Orchard API key.

## How it works

1. **Server side**, where your Orchard API key lives, mint a short-lived token
   scoped to **one sandbox** (screen only, or screen + input):

   ```python
   # Python
   from orchard_sdk import Orchard
   grant = Orchard.from_env().sandbox(uuid).embed_token(ttl=1800, input=True,
                                                         base="https://orchard.example.com")
   # -> {"token", "url", "uuid", "org", "workspace", "input", "expires_at"}
   ```

   ```ts
   // Node / TypeScript
   import { Orchard } from "@tryorchard/sdk";
   const grant = await Orchard.fromEnv().sandbox(uuid)
     .embedToken({ ttl: 1800, input: true, base: "https://orchard.example.com" });
   ```

   The token is a normal `orc_` key, but **capped**: it reaches *only* that
   sandbox's `uuid` and *only* the `screen` (and `input`) features, and it
   expires. Everything else — shell, files, frida, other sandboxes — is refused
   (403/404), enforced by the same scoping as any key. Hand the browser the
   `token`/`url`, never your real key.

2. **Client side**, show it. Two equivalent forms:

   **a) iframe** (any stack — even a non-JS backend can print this):

   ```html
   <iframe src="<grant.url>" style="width:360px;height:780px;border:0;border-radius:14px"></iframe>
   ```

   **b) React component** (`OrchardViewer.tsx` here, shipped as `@tryorchard/embed`):

   ```tsx
   import { OrchardViewer } from "@tryorchard/embed";

   <OrchardViewer url={grant.url} style={{ width: 360, height: 780 }} />
   // or from parts:
   <OrchardViewer uuid={uuid} token={token} input viewerBase="https://orchard.example.com" />
   ```

Both render the same hosted, chrome-less viewer at `/embed/<uuid>`, which polls the
screen and (when `input` is granted) posts taps and key presses back. There is no
login and no app chrome — just the device.

## Security notes

- The embed token is **short-lived, single-sandbox, screen(+input)-scoped**. Mint
  one per device per session with the smallest `ttl` and `input=false` unless the
  user needs to drive the device.
- The browser only ever holds the embed token. Your org API key stays on your
  server.
- Restrict who may frame the viewer with a `Content-Security-Policy:
  frame-ancestors` at your edge / reverse proxy for the `/embed` path, and set
  `ORCHARD_CORS_ORIGINS` on the backend to your app's origin(s).

## Files

- `OrchardViewer.tsx` — the React component (zero dependencies beyond React).
