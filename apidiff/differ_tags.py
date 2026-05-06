"""Diff OpenAPI operation tags between two spec versions."""

from typing import Any

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_operation_tags(spec: dict[str, Any]) -> dict[str, set[str]]:
    """Return a mapping of 'METHOD /path' -> set of tags."""
    result: dict[str, set[str]] = {}
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "head", "options", "trace"}:
                continue
            if not isinstance(operation, dict):
                continue
            key = f"{method.upper()} {path}"
            result[key] = set(operation.get("tags", []))
    return result


def _get_global_tags(spec: dict[str, Any]) -> set[str]:
    """Return the set of globally declared tag names."""
    return {tag["name"] for tag in spec.get("tags", []) if "name" in tag}


def diff_tags(old_spec: dict[str, Any], new_spec: dict[str, Any]) -> DiffReport:
    """Detect tag-related changes between two OpenAPI specs."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")
    changes: list[Change] = []

    # Global tag declarations
    old_global = _get_global_tags(old_spec)
    new_global = _get_global_tags(new_spec)

    for removed in old_global - new_global:
        changes.append(Change(
            change_type=ChangeType.REMOVED,
            severity=Severity.NON_BREAKING,
            path=f"tags/{removed}",
            operation=None,
            description=f"Global tag '{removed}' was removed from the tags declaration.",
        ))

    for added in new_global - old_global:
        changes.append(Change(
            change_type=ChangeType.ADDED,
            severity=Severity.NON_BREAKING,
            path=f"tags/{added}",
            operation=None,
            description=f"Global tag '{added}' was added to the tags declaration.",
        ))

    # Per-operation tags
    old_ops = _get_operation_tags(old_spec)
    new_ops = _get_operation_tags(new_spec)

    for op_key, old_tags in old_ops.items():
        if op_key not in new_ops:
            continue
        new_tags = new_ops[op_key]
        method, path = op_key.split(" ", 1)

        for removed_tag in old_tags - new_tags:
            changes.append(Change(
                change_type=ChangeType.REMOVED,
                severity=Severity.NON_BREAKING,
                path=path,
                operation=method,
                description=f"Tag '{removed_tag}' was removed from operation {method} {path}.",
            ))

        for added_tag in new_tags - old_tags:
            changes.append(Change(
                change_type=ChangeType.ADDED,
                severity=Severity.NON_BREAKING,
                path=path,
                operation=method,
                description=f"Tag '{added_tag}' was added to operation {method} {path}.",
            ))

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
