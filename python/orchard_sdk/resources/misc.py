"""Smaller resource namespaces: snapshots, templates, catalog, jobs, nodes."""
from __future__ import annotations

from typing import List, Any

from .. import _ws
from .._channels import SyncChannel
from .._http import HttpClient
from ..config import Config
from ..models import Job, SnapshotRow


class Snapshots:
    """``orchard.snapshots`` — every point-in-time snapshot in the org/workspace."""

    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> List[SnapshotRow]:
        """List all point snapshots visible to the caller."""
        return self._http.get("/snapshots")


class Templates:
    """``orchard.templates`` — reusable sandbox templates."""

    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> List[SnapshotRow]:
        """List available templates."""
        return self._http.get("/templates")

    def delete(self, pk: int) -> None:
        """Delete a template by id."""
        self._http.delete(f"/templates/{pk}")

    def launch(self, pk: int, name: str, **spec: Any) -> dict[str, Any]:
        """Launch a new sandbox from a template."""
        return self._http.post(f"/templates/{pk}/launch", json={"name": name, **spec})

    def import_avd(self, path: "str | Path", name: str, *, node: str,
                   provider: str = "android", install_image: bool = False,
                   timeout: float = 7200.0) -> dict[str, Any]:
        """Import a portable AVD profile ``.tar`` (from :meth:`Sandbox.export_avd`) onto
        ``node`` as a new, launchable template.

        The file is streamed **directly from this machine to the node** — the control
        plane only authorizes the upload and records the result, so a multi-GB profile
        never passes through (or is buffered by) the backend. This machine must be able
        to reach the node's agent. Set ``install_image`` to have the node download the
        base system image if it is missing.

        Returns the created template row (with the node's authoritative metadata).
        """
        from pathlib import Path
        p = Path(path)
        grant = self._http.post(f"/nodes/{node}/templates/import/begin",
                                json={"name": name, "provider": provider,
                                      "install_image": install_image})
        self._http.stream_file_to(grant["agent_url"], grant["upload_path"],
                                  grant["agent_token"], p, timeout=timeout)
        return self._http.post(f"/nodes/{node}/templates/import/commit",
                               json={"template_id": grant["template_id"],
                                     "provider": provider, "name": name})


class Catalog:
    """``orchard.catalog`` — what can be launched (images, presets, device types)."""

    def __init__(self, http: HttpClient):
        self._http = http

    def android(self) -> dict[str, Any]:
        """Android system images and device profiles."""
        return self._http.get("/android/catalog")

    def presets(self) -> dict[str, Any]:
        """iOS patch presets."""
        return self._http.get("/presets")

    def sim_device_types(self) -> dict[str, Any]:
        """iOS simulator device types and runtimes."""
        return self._http.get("/sim/device-types")

    def providers(self) -> List[dict[str, Any]]:
        """Per-node provider availability (platform admin only)."""
        return self._http.get("/providers")


class Jobs:
    """``orchard.jobs`` — background jobs (image downloads, vm creates)."""

    def __init__(self, http: HttpClient, cfg: Config):
        self._http = http
        self._cfg = cfg

    def list(self) -> List[Job]:
        """List jobs visible to the caller."""
        return self._http.get("/jobs")

    def cancel(self, node: str, job_id: str) -> dict[str, Any]:
        """Cancel a running job."""
        return self._http.post(f"/jobs/{node}/{job_id}/cancel")

    def logs(self, node: str, kind: str, name: str) -> SyncChannel:
        """Stream a job's log lines. ``with jobs.logs(...) as s: for line in s: ...``"""
        url = _ws.raw_ws_url(self._cfg, f"ws/jobs/{node}/{kind}/{name}/logs")
        return SyncChannel(url, _ws.decode_text)


class Nodes:
    """``orchard.nodes`` — infrastructure nodes (mostly platform-admin)."""

    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> List[dict[str, Any]]:
        """List placeable nodes."""
        return self._http.get("/nodes")

    def create(self, **cfg: Any) -> dict[str, Any]:
        """Enroll a node (``name``, ``agent_url``, ``agent_token``)."""
        return self._http.post("/nodes", json=cfg)

    def test(self, **cfg: Any) -> dict[str, Any]:
        """Probe an agent URL+token before enrolling."""
        return self._http.post("/nodes/test", json=cfg)

    def refresh(self, pk: int) -> dict[str, Any]:
        """Re-poll one node."""
        return self._http.post(f"/nodes/{pk}/refresh")

    def delete(self, pk: int) -> None:
        """Remove a node."""
        self._http.delete(f"/nodes/{pk}")
