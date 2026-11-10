"""The Orchard client facade — the one object users construct."""
from __future__ import annotations

from typing import Any

from . import config as _config
from ._http import HttpClient
from .config import Config
from .resources.keys import Keys
from .resources.misc import Catalog, Jobs, Nodes, Snapshots, Templates
from .resources.remote import Remote
from .resources.sandboxes import Sandbox, Sandboxes
from .resources.team import Team, Workspaces


class Orchard:
    """A client for an Orchard control plane.

    Construct it with a URL + API key, or :meth:`from_env` to read
    ``ORCHARD_API_URL`` / ``ORCHARD_API_KEY`` (+ optional ``ORCHARD_ORG`` / ``ORCHARD_WS``).

    >>> from orchard_sdk import Orchard
    >>> orchard = Orchard("https://orchard.example.com", "orc_…")
    >>> for s in orchard.sandboxes.list()["instances"]:
    ...     print(s["name"], s["state"])
    >>> orchard.sandbox("my-pixel").tag("payments", "#22c55e")

    The client holds an HTTP connection pool; use it as a context manager or call
    :meth:`close` when done.
    """

    def __init__(self, url: str | None = None, token: str | None = None,
                 org: str | None = None, ws: str | None = None, *, timeout: float = 60.0):
        self.config: Config = _config.from_env(url, token, org, ws, timeout)
        self._http = HttpClient(self.config)
        #: Fleet-wide sandbox listing and creation.
        self.sandboxes = Sandboxes(self._http, self.config)
        #: Point-in-time snapshots across the org.
        self.snapshots = Snapshots(self._http)
        #: Reusable sandbox templates.
        self.templates = Templates(self._http)
        #: API keys (including fine-grained scoped keys).
        self.keys = Keys(self._http)
        #: The organization, its members and invites.
        self.team = Team(self._http)
        #: Workspaces (teams) within the org.
        self.workspaces = Workspaces(self._http)
        #: What can be launched (images, presets, device types).
        self.catalog = Catalog(self._http)
        #: Background jobs.
        self.jobs = Jobs(self._http, self.config)
        #: Infrastructure nodes.
        self.nodes = Nodes(self._http)
        #: Remote (cloud) sandboxes and credentials.
        self.remote = Remote(self._http, self.config)

    @classmethod
    def from_env(cls, *, timeout: float = 60.0) -> "Orchard":
        """Build a client from the ``ORCHARD_*`` environment variables."""
        return cls(timeout=timeout)

    def me(self) -> dict[str, Any]:
        """The authenticated identity: orgs, active org/workspace, features."""
        return self._http.get("/me")

    def sandbox(self, selector: str) -> Sandbox:
        """Resolve a selector (uuid / uuid-prefix / name / tag) to a :class:`Sandbox` handle.

        Raises :class:`orchard_sdk.SelectorError` on zero or ambiguous matches.
        """
        inst = self.sandboxes.resolve(selector)
        return Sandbox(self._http, self.config, inst["uuid"])  # type: ignore[arg-type]

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> "Orchard":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
