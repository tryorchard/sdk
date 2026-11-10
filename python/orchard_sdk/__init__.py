"""Orchard SDK — a Python client for the Orchard mobile-sandbox control plane.

Quickstart::

    from orchard_sdk import Orchard

    orchard = Orchard.from_env()            # ORCHARD_API_URL + ORCHARD_API_KEY
    for s in orchard.sandboxes.list()["instances"]:
        print(s["name"], s["state"])

    sb = orchard.sandbox("my-pixel")        # by uuid / uuid-prefix / name / tag
    sb.tag("payments", "#22c55e")
    with sb.logs() as stream:
        for line in stream:
            print(line)

See https://docs.orchard.airoverflow.com for guides and the full API reference.
"""
from __future__ import annotations

from ._bridge import LocalBridge
from ._version import __version__
from .client import Orchard
from .config import Config, from_env
from .errors import ApiError, ChannelClosedError, OrchardError, SelectorError

__all__ = [
    "Orchard",
    "Config",
    "from_env",
    "OrchardError",
    "ApiError",
    "SelectorError",
    "ChannelClosedError",
    "LocalBridge",
    "__version__",
]
