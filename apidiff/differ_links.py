"""Detect breaking and non-breaking changes in OpenAPI response links."""

from __future__ import annotations

from typing import Any

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_links(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Collect all response links keyed by 'path:method:status:linkName'."""
    links: dict[str, dict[str, Any]] = {}
    paths = spec.get("paths", {})
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method not in (
                "get", "post", "put", "patch", "delete", "head", "options", "trace"
            ):
                continue
            responses = operation.get("responses", {})
            for status, response in responses.items():
                for link_name, link_obj in response.get("links", {}).items():
                    key = f"{path}:{method}:{status}:{link_name}"
                    links[key] = link_obj
    return links


def diff_links(
    old_spec: dict[str, Any],
    new_spec: dict[str, Any],
) -> DiffReport:
    """Compare response links between two OpenAPI specs.

    Removing a link is non-breaking (links are hints for clients).
    Changing the operationId or operationRef of an existing link is breaking
    because clients relying on the link would be misdirected.
    Adding a link is non-breaking.
    """
    old_ver = old_spec.get("info", {}).get("version", "unknown")
    new_ver = new_spec.get("info", {}).get("version", "unknown")

    old_links = _get_links(old_spec)
    new_links = _get_links(new_spec)

    changes: list[Change] = []

    for key, old_link in old_links.items():
        path = key.split(":")[0]
        if key not in new_links:
            changes.append(
                Change(
                    change_type=ChangeType.REMOVED,
                    severity=Severity.NON_BREAKING,
                    path=path,
                    description=f"Response link '{key}' removed.",
                )
            )
            continue

        new_link = new_links[key]
        for field in ("operationId", "operationRef"):
            old_val = old_link.get(field)
            new_val = new_link.get(field)
            if old_val is not None and old_val != new_val:
                changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        severity=Severity.BREAKING,
                        path=path,
                        description=(
                            f"Response link '{key}' field '{field}' changed "
                            f"from '{old_val}' to '{new_val}'."
                        ),
                    )
                )

    for key in new_links:
        if key not in old_links:
            path = key.split(":")[0]
            changes.append(
                Change(
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    path=path,
                    description=f"Response link '{key}' added.",
                )
            )

    return DiffReport(
        old_version=old_ver,
        new_version=new_ver,
        changes=changes,
    )
