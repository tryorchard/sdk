"""Resolve a human-friendly sandbox selector to a concrete instance.

Precedence (first non-empty tier wins): exact uuid, uuid prefix, exact
name/display_name, then tag. Only node sandboxes (those with a ``uuid``) are
candidates; remote cloud rows are addressed by ``record_id`` elsewhere.
"""
from __future__ import annotations

from typing import Any, Callable

from .errors import SelectorError


def _candidates(instances: list[Any]) -> list[dict[str, Any]]:
    return [i for i in instances if i.get("uuid")]


def _fmt(matches: list[Any]) -> str:
    return "\n".join(
        f"  {(i.get('name') or '?'):<24} {i['uuid']}  tag={i.get('tag') or '-'}  node={i.get('node') or '-'}"
        for i in matches)


def resolve_all(instances: list[Any], selector: str) -> list[dict[str, Any]]:
    """Every sandbox the selector matches, by the first precedence tier that hits.

    Tag selectors legitimately match many; single-target callers use
    :func:`resolve`, which rejects more than one.
    """
    cands = _candidates(instances)
    tiers: tuple[Callable[[dict[str, Any]], bool], ...] = (
        lambda i: i["uuid"] == selector,
        lambda i: str(i["uuid"]).startswith(selector),
        lambda i: selector in (i.get("name"), i.get("display_name")),
        lambda i: bool(selector) and i.get("tag") == selector,
    )
    for pred in tiers:
        hit = [i for i in cands if pred(i)]
        if hit:
            return hit
    return []


def resolve(instances: list[Any], selector: str) -> dict[str, Any]:
    """Exactly one sandbox, or :class:`SelectorError` (zero or ambiguous match)."""
    matches = resolve_all(instances, selector)
    if not matches:
        raise SelectorError(f"no sandbox matches {selector!r}")
    if len(matches) > 1:
        raise SelectorError(
            f"{selector!r} matches {len(matches)} sandboxes — be more specific:\n"
            + _fmt(matches))
    return matches[0]
