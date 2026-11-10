"""Stream a sandbox's logs. Usage: python stream_logs.py <selector>"""
import sys

from orchard_sdk import Orchard

if len(sys.argv) < 2:
    sys.exit(__doc__)

with Orchard.from_env() as orchard:
    sb = orchard.sandbox(sys.argv[1])
    print(f"streaming logs from {sys.argv[1]} ({sb.uuid[:8]}), Ctrl-C to stop")
    with sb.logs() as stream:
        for line in stream:
            print(line)
