"""The sync REST transport: one httpx client that knows Orchard's base URL,
auth header, tenancy headers, and how a server error becomes an :class:`ApiError`.

Internal — consumers use :class:`orchard_sdk.Orchard` and its resource namespaces,
not this class directly.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from .config import Config
from .errors import ApiError


def _detail(r: httpx.Response) -> str:
    try:
        body = r.json()
    except Exception:
        return r.text[:300].strip()
    if isinstance(body, dict):
        return str(body.get("detail") or body)
    return str(body)


class HttpClient:
    """Thin synchronous wrapper over ``httpx.Client`` scoped to one Orchard org/workspace."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        headers = {"Authorization": f"Bearer {cfg.token}"}
        if cfg.org:
            headers["X-Orchard-Org"] = cfg.org
        if cfg.ws:
            headers["X-Orchard-Workspace"] = cfg.ws
        self._c = httpx.Client(base_url=cfg.api_base, headers=headers, timeout=cfg.timeout)

    def close(self) -> None:
        self._c.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _request(self, method: str, path: str, **kw: Any) -> Any:
        r = self._c.request(method, path, **kw)
        if r.status_code >= 400:
            raise ApiError(r.status_code, _detail(r))
        if r.status_code == 204 or not r.content:
            return None
        return r.json()

    def get(self, path: str, **kw: Any) -> Any:
        return self._request("GET", path, **kw)

    def get_content(self, path: str, **kw: Any) -> bytes:
        """A GET whose body is raw bytes (screenshots, mitm CA)."""
        r = self._c.request("GET", path, **kw)
        if r.status_code >= 400:
            raise ApiError(r.status_code, _detail(r))
        return r.content

    def post(self, path: str, json: Any = None, **kw: Any) -> Any:
        return self._request("POST", path, json=json, **kw)

    def patch(self, path: str, json: Any = None, **kw: Any) -> Any:
        return self._request("PATCH", path, json=json, **kw)

    def delete(self, path: str, **kw: Any) -> Any:
        return self._request("DELETE", path, **kw)

    def post_files(self, path: str, files: list[tuple[str, Path]],
                   data: dict[str, Any] | None = None) -> Any:
        """multipart POST (APK/IPA install, file upload). ``files`` is ``[(field, Path)]``."""
        handles = [(field, (p.name, p.open("rb"))) for field, p in files]
        try:
            return self._request("POST", path, files=handles, data=data or {})
        finally:
            for _, (_, fh) in handles:
                fh.close()

    def download(self, absolute_url: str, dest: Path) -> int:
        """Stream a signed-grant URL (full URL incl. ``?token=``) to a file.

        The grant is itself the credential, so this request carries **no**
        Authorization header. Returns the number of bytes written.
        """
        total = 0
        with httpx.Client(timeout=300.0) as raw, raw.stream("GET", absolute_url) as r:
            if r.status_code >= 400:
                raise ApiError(r.status_code, _detail(r))
            with dest.open("wb") as fh:
                for chunk in r.iter_bytes(65536):
                    fh.write(chunk)
                    total += len(chunk)
        return total
