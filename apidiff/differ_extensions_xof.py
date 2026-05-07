"""Detect breaking changes in oneOf/anyOf schema composition."""
from __future__ import annotations

from typing import Any

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_schemas(spec: dict[str, Any]) -> dict[str, Any]:
    return spec.get("components", {}).get("schemas", {})


def _collect_xof(schema: dict[str, Any]) -> dict[str, list[str]]:
    """Return a dict with keys 'oneOf' and 'anyOf', each a list of $ref strings."""
    result: dict[str, list[str]] = {}
    for keyword in ("oneOf", "anyOf"):
        entries = schema.get(keyword, [])
        if entries:
            result[keyword] = [
                e.get("$ref", str(e)) for e in entries if isinstance(e, dict)
            ]
    return result


def diff_xof(
    old_spec: dict[str, Any],
    new_spec: dict[str, Any],
) -> DiffReport:
    """Diff oneOf/anyOf composition changes across component schemas."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    old_schemas = _get_schemas(old_spec)
    new_schemas = _get_schemas(new_spec)
    changes: list[Change] = []

    all_names = set(old_schemas) | set(new_schemas)
    for name in sorted(all_names):
        old_xof = _collect_xof(old_schemas.get(name, {}))
        new_xof = _collect_xof(new_schemas.get(name, {}))

        for keyword in ("oneOf", "anyOf"):
            old_refs = set(old_xof.get(keyword, []))
            new_refs = set(new_xof.get(keyword, []))

            for removed in sorted(old_refs - new_refs):
                changes.append(
                    Change(
                        path=f"#/components/schemas/{name}/{keyword}",
                        operation=None,
                        change_type=ChangeType.REMOVED,
                        severity=Severity.BREAKING,
                        description=(
                            f"Removed '{removed}' from {keyword} in schema '{name}'; "
                            "existing consumers relying on this variant will break."
                        ),
                    )
                )

            for added in sorted(new_refs - old_refs):
                changes.append(
                    Change(
                        path=f"#/components/schemas/{name}/{keyword}",
                        operation=None,
                        change_type=ChangeType.ADDED,
                        severity=Severity.NON_BREAKING,
                        description=(
                            f"Added '{added}' to {keyword} in schema '{name}'."
                        ),
                    )
                )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
