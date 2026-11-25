"""Typed shapes for Orchard's wire JSON.

These mirror the TypeScript SDK types; the control plane is the source of truth,
so they are intentionally permissive ``TypedDict``\\s (no runtime validation):
a response is returned as-is and annotated for editor/mypy help.
"""
from __future__ import annotations

from typing import Any, Literal, TypedDict

Platform = Literal["ios", "android"]
Provider = Literal["vphone", "baguette", "android", "cuttlefish", "qemu", "e2b", "daytona", "modal"]


class Capability(TypedDict):
    key: str
    supported: bool
    available: bool
    reason: str


class Hardware(TypedDict, total=False):
    cpu: int | None
    memory_mb: int | None
    disk_bytes: int | None
    udid: str | None
    screen_points: dict[str, int]


class Runtime(TypedDict, total=False):
    state: str
    pid: int | None
    adopted: bool
    guest_ip: str | None
    guest_os: str | None
    uptime_s: int | None
    log_lines: int
    serial: str | None
    error: str | None


class Instance(TypedDict, total=False):
    """A sandbox as returned by ``GET /api/instances`` and ``/api/sandboxes/<uuid>``."""
    id: str
    uuid: str | None
    provider: Provider
    platform: Platform
    location: Literal["node", "remote"]
    record_id: int
    external_id: str
    key: str
    name: str
    display_name: str
    node: str | None
    node_id: int
    state: str
    variant: str
    os_version: str | None
    os_build: str | None
    mode: str
    mode_label: str
    owner: str | None
    notes: str
    tag: str
    tag_color: str
    read_only: bool
    unmanaged: bool
    can_manage: bool
    image: str
    image_installed: bool
    family: str | None
    device: str | None
    files_home: str
    buttons: list[str]
    capabilities: dict[str, Capability]
    hardware: Hardware
    runtime: Runtime
    vnc: dict[str, Any]
    screen: dict[str, Any]
    expires_at: str | None
    auto_action: str


class InstanceList(TypedDict):
    instances: list[Instance]
    errors: list[dict[str, Any]]


class KernelOptions(TypedDict, total=False):
    """Android kernel-modularity options for :meth:`Sandboxes.create` /
    :meth:`Templates.launch`. All optional; they serialize into the create body.

    ``kernel``/``ramdisk`` name files in the node kernel store (see
    :class:`Nodes`); ``kernel_cmdline`` is extra boot cmdline; ``boot_props`` are
    guest ``ro.*``/``persist.*`` props; ``kernel_gdb`` boots with a halted gdb
    stub (bridge with :meth:`Sandbox.gdb_bridge`)."""
    rooted: bool
    kernel_gdb: bool
    kernel: str
    ramdisk: str
    kernel_cmdline: str
    boot_props: dict[str, str]
    device_profile: str
    isolated: bool


class KernelFile(TypedDict):
    """A kernel/ramdisk/vmlinux file in a node's kernel store."""
    name: str
    size: int


class SnapshotRow(TypedDict, total=False):
    id: int
    uuid: str
    name: str
    kind: Literal["point", "template"]
    node: str
    provider: str
    platform: Platform
    instance_key: str
    instance_uuid: str | None
    template_id: str
    visibility: Literal["private", "org"]
    description: str
    created_by: str | None
    created_at: str
    meta: dict[str, Any]


class RecordingRow(TypedDict, total=False):
    """A session recording's metadata, as returned by the ``recording/*`` endpoints."""
    id: str
    kind: str
    key: str
    status: str
    started: float
    duration: float
    actions: int
    video: bool
    video_bytes: int


class Job(TypedDict, total=False):
    id: str
    node: str
    kind: str
    target: str
    state: str
    phase: str
    progress: int | None
    exit_code: int | None
    started_at: float
    finished_at: float | None
    elapsed_s: float


class ApiKey(TypedDict, total=False):
    """A row from ``GET /api/tokens``. The raw secret is only present in the
    ``POST`` create response (shown once)."""
    id: int
    name: str
    hint: str
    token: str
    created_at: str
    expires_at: str | None
    last_used: str | None
    sandbox_uuids: list[str]
    tag: str
    allowed_features: list[str] | None
