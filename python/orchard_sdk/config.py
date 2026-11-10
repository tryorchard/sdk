"""Connection configuration, resolved from explicit arguments or the environment.

Primary environment variables:

* ``ORCHARD_API_URL`` — the control-plane URL, e.g. ``https://orchard.example.com``
  (``ORCHARD_URL`` is accepted as a legacy alias).
* ``ORCHARD_API_KEY`` — an Orchard API key (``orc_…``) or a JWT access token.
* ``ORCHARD_ORG`` / ``ORCHARD_WS`` — optional org / workspace slug overrides.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass
class Config:
    """Resolved connection settings shared by the REST and WebSocket transports.

    Args:
        url: Control-plane base URL (scheme + host), e.g. ``https://orchard.example.com``.
        token: API key (``orc_…``) or JWT access token sent as ``Authorization: Bearer``.
        org: Optional organization slug (``X-Orchard-Org``). Ignored for API keys,
            which are bound to the org they were minted in.
        ws: Optional workspace slug (``X-Orchard-Workspace``).
        timeout: Default REST request timeout in seconds.
    """

    url: str
    token: str
    org: str | None = None
    ws: str | None = None
    timeout: float = 60.0

    @property
    def api_base(self) -> str:
        """REST base URL, e.g. ``https://host/api``."""
        return self.url.rstrip("/") + "/api"

    @property
    def ws_base(self) -> str:
        """WebSocket origin, e.g. ``wss://host`` (any path/query on ``url`` is dropped)."""
        parts = urlsplit(self.url)
        scheme = "wss" if parts.scheme == "https" else "ws"
        return f"{scheme}://{parts.netloc}"


def from_env(
    url: str | None = None,
    token: str | None = None,
    org: str | None = None,
    ws: str | None = None,
    timeout: float = 60.0,
) -> Config:
    """Build a :class:`Config`, letting explicit arguments win over environment
    variables. Raises :class:`ValueError` if neither a URL nor a token can be found.

    >>> cfg = from_env()  # reads ORCHARD_API_URL + ORCHARD_API_KEY
    """
    url = url or os.environ.get("ORCHARD_API_URL") or os.environ.get("ORCHARD_URL")
    token = token or os.environ.get("ORCHARD_API_KEY")
    org = org or os.environ.get("ORCHARD_ORG")
    ws = ws or os.environ.get("ORCHARD_WS")
    if not url:
        raise ValueError("no Orchard URL: pass url= or set ORCHARD_API_URL")
    if not token:
        raise ValueError("no Orchard token: pass token= or set ORCHARD_API_KEY")
    return Config(url=url, token=token, org=org, ws=ws, timeout=timeout)
