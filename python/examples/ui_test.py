"""Drive a login screen, then roll the sandbox back to a clean snapshot.

Usage: python ui_test.py <selector> <package>
"""
import sys
import time

from orchard_sdk import Orchard

if len(sys.argv) < 3:
    sys.exit(__doc__)
selector, package = sys.argv[1:3]

with Orchard.from_env() as orchard:
    sb = orchard.sandbox(selector)
    sb.snapshots.create("before-ui-test")
    try:
        sb.launch(package)
        time.sleep(2)
        sb.tap_text("Email")
        sb.text("demo@example.com")
        sb.tap_text("Password")
        sb.text("hunter2")
        sb.tap_text("Sign in")
        time.sleep(2)

        labels = str(sb.describe_ui())
        print("PASS" if "Welcome" in labels else "FAIL: no welcome screen")
        with open("after-login.png", "wb") as f:
            f.write(sb.screenshot())
    finally:
        sb.snapshots.restore("before-ui-test")
        sb.snapshots.delete("before-ui-test")
