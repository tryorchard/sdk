"""Organization, members and invites (``orchard.team``), and workspaces
(``orchard.workspaces``)."""
from __future__ import annotations

from typing import List, Any

from .._http import HttpClient


class _Members:
    def __init__(self, http: HttpClient, base: str):
        self._http = http
        self._base = base

    def list(self) -> List[dict[str, Any]]:
        """List members."""
        return self._http.get(f"{self._base}/members")

    def edit(self, pk: int, **fields: Any) -> dict[str, Any]:
        """Change a member's ``role``/``denied_features``/limits."""
        return self._http.patch(f"{self._base}/members/{pk}", json=fields)

    def remove(self, pk: int) -> None:
        """Remove a member."""
        self._http.delete(f"{self._base}/members/{pk}")


class _Invites:
    def __init__(self, http: HttpClient, base: str):
        self._http = http
        self._base = base

    def list(self) -> List[dict[str, Any]]:
        """List pending invites."""
        return self._http.get(f"{self._base}/invites")

    def create(self, role: str = "member") -> dict[str, Any]:
        """Create an invite; the response ``token`` is the one-time join credential."""
        return self._http.post(f"{self._base}/invites", json={"role": role})

    def delete(self, pk: int) -> None:
        """Revoke an invite."""
        self._http.delete(f"{self._base}/invites/{pk}")


class Team:
    """``orchard.team`` — the active organization, its members and invites."""

    def __init__(self, http: HttpClient):
        self._http = http
        self.members = _Members(http, "/org")
        self.invites = _Invites(http, "/org")

    def get(self) -> dict[str, Any]:
        """The org, its usage, features and member count."""
        return self._http.get("/org")

    def edit(self, **fields: Any) -> dict[str, Any]:
        """Change org fields (e.g. ``name``) — org admin only."""
        return self._http.patch("/org", json=fields)

    def invite_info(self, token: str) -> dict[str, Any]:
        """Describe an invite token (unauthenticated-friendly)."""
        return self._http.get(f"/invites/{token}")

    def accept_invite(self, token: str, **account: Any) -> dict[str, Any]:
        """Accept an invite (optionally creating an account with
        ``username``/``password``/``email``)."""
        return self._http.post(f"/invites/{token}", json=account)


class _Workspace:
    def __init__(self, http: HttpClient, slug: str):
        self._http = http
        self._base = f"/workspaces/{slug}"
        self.slug = slug
        self.members = _Members(http, self._base)
        self.invites = _Invites(http, self._base)

    def edit(self, **fields: Any) -> dict[str, Any]:
        """Change workspace fields (e.g. ``name``)."""
        return self._http.patch(self._base, json=fields)

    def delete(self) -> None:
        """Delete the workspace (must be empty; cannot delete the default)."""
        self._http.delete(self._base)


class Workspaces:
    """``orchard.workspaces`` — teams within the org."""

    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> List[dict[str, Any]]:
        """List the caller's workspaces (via ``/api/me``)."""
        return self._http.get("/me").get("workspaces", [])

    def create(self, name: str, slug: str | None = None) -> dict[str, Any]:
        """Create a workspace (org admin)."""
        body: dict[str, Any] = {"name": name}
        if slug:
            body["slug"] = slug
        return self._http.post("/workspaces", json=body)

    def get(self, slug: str) -> "_Workspace":
        """A handle to one workspace by slug."""
        return _Workspace(self._http, slug)
