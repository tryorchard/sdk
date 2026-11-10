"""Mint a 30-day key that can only read logs and files of one sandbox.

Usage: python scoped_key.py <selector>
"""
import sys

from orchard_sdk import Orchard

if len(sys.argv) < 2:
    sys.exit(__doc__)

with Orchard.from_env() as orchard:
    sb = orchard.sandbox(sys.argv[1])
    key = orchard.keys.create(
        "ci-logs-only",
        sandbox_uuids=[sb.uuid],
        allowed_features=["logs", "files"],
        expires_in_days=30,
    )
    print("new scoped key (shown once):", key["token"])
