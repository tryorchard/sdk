"""Live smoke against a running Orchard. Skipped unless ORCHARD_SMOKE=1.

Set ORCHARD_API_URL + ORCHARD_API_KEY (an orc_ key or a JWT access token) and
ORCHARD_SMOKE_UUID (a sandbox selector, default "cuttlefish").
"""
import itertools
import os

import pytest

from orchard_sdk import Orchard

pytestmark = pytest.mark.skipif(os.environ.get("ORCHARD_SMOKE") != "1",
                                reason="set ORCHARD_SMOKE=1 to run live")


def test_live_list_tag_logs():
    sel = os.environ.get("ORCHARD_SMOKE_UUID", "cuttlefish")
    with Orchard.from_env() as orchard:
        data = orchard.sandboxes.list()
        assert "instances" in data
        sb = orchard.sandbox(sel)
        sb.tag("smoke")
        assert sb.get().get("tag") == "smoke"
        # read a few log lines then stop (if the sandbox is running)
        if sb.get().get("state") == "running":
            with sb.logs() as stream:
                lines = list(itertools.islice(stream, 3))
            assert lines  # got at least one line
