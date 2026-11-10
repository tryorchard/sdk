"""API keys, including fine-grained scoped keys."""
from __future__ import annotations

from typing import List, Any

from .._http import HttpClient
from ..models import ApiKey


class Keys:
    """The ``orchard.keys`` namespace — manage API keys (``/api/tokens``)."""

    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> List[ApiKey]:
        """List the caller's API keys (metadata only; secrets are never returned)."""
        return self._http.get("/tokens")

    def create(self, name: str, *, sandbox_uuids: List[str] | None = None,
               tag: str | None = None, allowed_features: List[str] | None = None,
               expires_in_days: int | None = None) -> ApiKey:
        """Mint an API key; the raw secret is in the response ``token`` field (shown once).

        Scope it by passing any of ``sandbox_uuids`` (specific sandboxes), ``tag``
        (every sandbox carrying that tag, now and future), and ``allowed_features``
        (a capability subset). Omit all three for a full org-wide key.

        >>> k = orchard.keys.create("ci", sandbox_uuids=[sb.uuid],
        ...                         allowed_features=["logs", "files"], expires_in_days=30)
        >>> print(k["token"])  # store it now
        """
        body: dict[str, Any] = {"name": name}
        if expires_in_days is not None:
            body["expires_in_days"] = expires_in_days
        if sandbox_uuids is not None:
            body["sandbox_uuids"] = sandbox_uuids
        if tag is not None:
            body["tag"] = tag
        if allowed_features is not None:
            body["capabilities"] = allowed_features
        return self._http.post("/tokens", json=body)

    def delete(self, key_id: int) -> None:
        """Revoke a key by id."""
        self._http.delete(f"/tokens/{key_id}")
