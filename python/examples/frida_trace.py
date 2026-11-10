"""Stream Activity.onResume calls from an Android app with frida.

Usage: python frida_trace.py <selector> <package>
"""
import sys

from orchard_sdk import Orchard

if len(sys.argv) < 3:
    sys.exit(__doc__)
selector, package = sys.argv[1:3]

SCRIPT = """
Java.perform(() => {
  const Activity = Java.use("android.app.Activity");
  Activity.onResume.implementation = function () {
    send("onResume " + this.getClass().getName());
    this.onResume();
  };
});
"""

with Orchard.from_env() as orchard:
    sb = orchard.sandbox(selector)
    status = sb.frida.status()
    if not status.get("installed"):
        sb.frida.install()
    elif not status.get("running"):
        sb.frida.start()

    sb.launch(package)
    with sb.frida.stream(SCRIPT, package, timeout=60) as messages:
        for msg in messages:
            print(msg)
