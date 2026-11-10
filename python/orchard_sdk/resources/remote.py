"""Remote (cloud) sandboxes and provider credentials — ``orchard.remote``.

Remote sandboxes run on cloud providers (e2b/daytona/modal) rather than nodes,
and are addressed by their numeric ``record_id`` (not a uuid)."""
from __future__ import annotations

from pathlib import Path
from typing import List, Any

from .. import _ws
from .._channels import SyncChannel
from .._http import HttpClient
from ..config import Config


class Remote:
    """The ``orchard.remote`` namespace."""

    def __init__(self, http: HttpClient, cfg: Config):
        self._http = http
        self._cfg = cfg

    def credentials(self) -> List[dict[str, Any]]:
        """List stored provider credentials."""
        return self._http.get("/credentials")

    def add_credential(self, provider: str, key: str, label: str | None = None,
                       config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Store (and verify) a provider API key."""
        body: dict[str, Any] = {"provider": provider, "key": key}
        if label:
            body["label"] = label
        if config:
            body["config"] = config
        return self._http.post("/credentials", json=body)

    def delete_credential(self, ref: int | str) -> None:
        """Delete a stored credential."""
        self._http.delete(f"/credentials/{ref}")

    def catalog(self) -> dict[str, Any]:
        """Which cloud providers are available/configured."""
        return self._http.get("/remote/catalog")

    def create(self, provider: str, name: str, **spec: Any) -> dict[str, Any]:
        """Create a remote sandbox (``image``/``cpu``/``memory_mb``/``region``/``ttl_minutes``…)."""
        return self._http.post("/remote/create", json={"provider": provider, "name": name, **spec})

    def get(self, ref: int | str) -> dict[str, Any]:
        """Fetch a remote sandbox by uuid (or legacy record id)."""
        return self._http.get(f"/remote/{ref}")

    def delete(self, ref: int | str) -> None:
        """Terminate a remote sandbox."""
        self._http.delete(f"/remote/{ref}")

    def start(self, ref: int | str) -> dict[str, Any]:
        """Start a remote sandbox."""
        return self._http.post(f"/remote/{ref}/start")

    def stop(self, ref: int | str) -> dict[str, Any]:
        """Stop a remote sandbox."""
        return self._http.post(f"/remote/{ref}/stop")

    def upload(self, ref: int | str, local: str | Path, path: str | None = None) -> dict[str, Any]:
        """Upload a file into a remote sandbox."""
        data = {"path": path} if path else None
        return self._http.post_files(f"/remote/{ref}/files", files=[("file", Path(local))], data=data)

    def shell(self, ref: int | str) -> SyncChannel:
        """An interactive shell to a remote sandbox (``with remote.shell(ref) as s: ...``)."""
        return SyncChannel(_ws.raw_ws_url(self._cfg, f"ws/remote/{ref}/shell"), _ws.decode_text)

    def download(self, ref: int | str, path: str, local: str | Path | None = None) -> int:
        """Download a file from a remote sandbox. Writes to ``local`` (or the
        file's basename in the cwd); returns the number of bytes written."""
        data = self._http.get_content(f"/remote/{ref}/files/download", params={"path": path})
        dest = Path(local) if local else Path(path.rstrip("/").rsplit("/", 1)[-1] or "download")
        dest.write_bytes(data)
        return len(data)

    def logs(self, ref: int | str) -> SyncChannel:
        """Stream a remote sandbox's logs (``with remote.logs(ref) as s: ...``)."""
        return SyncChannel(_ws.raw_ws_url(self._cfg, f"ws/remote/{ref}/logs"), _ws.decode_text)

    def metrics(self, ref: int | str) -> dict[str, Any]:
        """Live resource sample (cpu/mem/uptime, sampled inside the sandbox)."""
        return self._http.get(f"/remote/{ref}/metrics")
