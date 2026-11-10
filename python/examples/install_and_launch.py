"""Install an APK, launch it and save a screenshot.

Usage: python install_and_launch.py <selector> <app.apk> <package>
"""
import sys
import time

from orchard_sdk import Orchard

if len(sys.argv) < 4:
    sys.exit(__doc__)
selector, apk, package = sys.argv[1:4]

with Orchard.from_env() as orchard:
    sb = orchard.sandbox(selector)
    if sb.get()["state"] != "running":
        sb.start()

    sb.apps.install(apk)
    sb.launch(package)
    time.sleep(3)

    with open("screenshot.png", "wb") as f:
        f.write(sb.screenshot())
    print("installed", package, "and saved screenshot.png")
