"""Smaller resource namespaces: snapshots, templates, catalog, jobs, nodes."""
from __future__ import annotations

from pathlib import Path
from typing import List, Any

from .. import _ws
from .._channels import SyncChannel
from .._http import HttpClient
from ..config import Config
from ..models import Job, KernelFile, KernelOptions, SnapshotRow


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

    def launch(self, pk: int, name: str, *, kernel_options: KernelOptions | None = None,
               **spec: Any) -> dict[str, Any]:
        """Launch a new sandbox from a template. ``kernel_options`` is a typed
        :class:`~orchard_sdk.models.KernelOptions` bag of Android kernel-modularity
        fields merged into the launch body (same keys may be passed inline)."""
        return self._http.post(f"/templates/{pk}/launch",
                               json={"name": name, **spec, **(kernel_options or {})})

    def import_avd(self, path: str | Path, name: str, *, node: str,
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

    # -- kernel store (modular kernels: boot a custom kernel, or pull vmlinux for gdb) --
    def kernels(self, node: str) -> List[KernelFile]:
        """List ``node``'s kernel/ramdisk/vmlinux files. Each ``{name, size}`` —
        a ``name`` is usable as ``kernel=``/``ramdisk=`` at create."""
        return (self._http.get(f"/kernels/{node}") or {}).get("kernels", [])

    def upload_kernel(self, node: str, path: str | Path) -> KernelFile:
        """Upload a local kernel/ramdisk/vmlinux file to ``node``'s store
        (admin-gated). Returns the stored ``{name, size}``."""
        return self._http.post_files(f"/kernels/{node}", files=[("file", Path(path))])

    def download_kernel(self, node: str, name: str, dest: str | Path,
                        *, timeout: float = 3600.0) -> int:
        """Download kernel file ``name`` from ``node`` to ``dest`` (e.g. a
        ``vmlinux`` for local gdb). Returns the number of bytes written."""
        return self._http.stream_to_file(f"/kernels/{node}/{name}", Path(dest), timeout=timeout)

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


class Relay:
    """``orchard.relay`` — physical device relays.

    A device relay is a genuine phone holding an outbound socket to the control
    plane; emulators relay their keymint attestation / Play-Integrity-token requests
    to it (DroidGuard runs on the real device, which passes). Use this to see which
    phones are connected and to verify one is relaying properly.
    """

    def __init__(self, http: HttpClient):
        self._http = http

    def devices(self) -> List[dict[str, Any]]:
        """List physical device-relay nodes with live connection + capability status.

        Each row: ``{id, name, connected, capabilities, state, last_heartbeat}``.
        """
        return (self._http.get("/nodes/relay/devices") or {}).get("devices", [])

    def _resolve(self, device: "int | str") -> int:
        if isinstance(device, int):
            return device
        for d in self.devices():
            if device in (d["name"], str(d["id"])):
                return d["id"]
        raise ValueError(f"no relay device {device!r}")

    def test(self, device: "int | str") -> dict[str, Any]:
        """Force a relay round-trip to a device (by id or name) to verify it is
        connected and relaying properly. Returns
        ``{ok, connected, latency_ms, capabilities, detail}`` — never raises on a
        down device, so it is safe to poll as a health check."""
        return self._http.post(f"/nodes/{self._resolve(device)}/relay/test")

    def enroll_token(self, name: str = "") -> dict[str, Any]:
        """Mint a single-use enrollment token for your organization. Install the
        orchard-node app on a phone and paste the returned ``token`` to bind that one
        device to this org. Returns ``{token, hint, name, expires_at}`` — the token is
        shown ONCE."""
        return self._http.post("/nodes/relay/enroll-token", json={"name": name})

    def enroll_tokens(self) -> List[dict[str, Any]]:
        """List this org's enrollment tokens (hashes only; never the raw token)."""
        return (self._http.get("/nodes/relay/enroll-token") or {}).get("tokens", [])
