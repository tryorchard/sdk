"""Expose a sandbox's adb on a local port and run adb against it.

Usage: python adb_bridge.py <selector>
"""
import subprocess
import sys

from orchard_sdk import Orchard

if len(sys.argv) < 2:
    sys.exit(__doc__)

with Orchard.from_env() as orchard:
    sb = orchard.sandbox(sys.argv[1])
    with sb.adb_bridge() as bridge:
        serial = f"127.0.0.1:{bridge.port}"
        subprocess.run(["adb", "connect", serial], check=True)
        subprocess.run(["adb", "-s", serial, "shell", "getprop", "ro.build.version.release"], check=True)
        input(f"adb is reachable at {serial}; press Enter to close the bridge")
        subprocess.run(["adb", "disconnect", serial])
