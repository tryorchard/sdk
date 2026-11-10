# Examples

Set `ORCHARD_API_URL` and `ORCHARD_API_KEY`, then run any script with `python <script> <args>`.

| Script | What it does |
| --- | --- |
| `quickstart.py` | Print the caller and list sandboxes |
| `stream_logs.py <selector>` | Follow a sandbox's logs |
| `scoped_key.py <selector>` | Mint a 30-day key limited to one sandbox's logs and files |
| `install_and_launch.py <selector> <apk> <package>` | Install an APK, launch it, save a screenshot |
| `ui_test.py <selector> <package>` | Drive a login form, check the result, roll back to a snapshot |
| `frida_trace.py <selector> <package>` | Stream `Activity.onResume` calls via frida |
| `capture_traffic.py <selector>` | Save the mitm CA and print HTTP(S) flows |
| `adb_bridge.py <selector>` | Expose the sandbox's adb on a local port |
