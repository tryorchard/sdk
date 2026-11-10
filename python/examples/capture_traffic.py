"""Save the mitm CA and print HTTP(S) flows as the app makes them.

Start capture for the sandbox in the Orchard console first.
Usage: python capture_traffic.py <selector>
"""
import sys

from orchard_sdk import Orchard

if len(sys.argv) < 2:
    sys.exit(__doc__)

with Orchard.from_env() as orchard:
    sb = orchard.sandbox(sys.argv[1])
    with open("orchard-mitm-ca.pem", "wb") as f:
        f.write(sb.mitm_ca())

    with sb.mitm_flows() as flows:
        for flow in flows:
            print(flow["method"], flow["status"], f"{flow['scheme']}://{flow['host']}{flow['path']}")
