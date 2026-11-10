# Examples

Run `npm install && npm run build` once, set `ORCHARD_API_URL` and `ORCHARD_API_KEY`, then:

```bash
node --experimental-strip-types examples/<script>.mts <args>
```

(Node 23.6+ runs `.mts` without the flag.)

| Script | What it does |
| --- | --- |
| `quickstart.mts` | Print the caller and list sandboxes |
| `stream-logs.mts <selector>` | Follow a sandbox's logs |
| `scoped-key.mts <selector>` | Mint a 30-day key limited to one sandbox's logs and files |
| `install-and-launch.mts <selector> <apk> <package>` | Install an APK, launch it, save a screenshot |
| `ui-test.mts <selector> <package>` | Drive a login form, check the result, roll back to a snapshot |
| `frida-trace.mts <selector> <package>` | Stream `Activity.onResume` calls via frida |
| `capture-traffic.mts <selector>` | Save the mitm CA and print HTTP(S) flows |
