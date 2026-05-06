"""Detect deprecated field changes in request/response schemas."""

from typing import Any, Dict

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_operations(spec: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return a flat map of (path, method) -> operation dict."""
    ops = {}
    for path, path_item in spec.get("paths", {}).items():
        for method in ("get", "post", "put", "patch", "delete", "head", "options", "trace"):
            op = path_item.get(method)
            if op:
                ops[(path, method)] = op
    return ops


def _is_deprecated(op: Dict[str, Any]) -> bool:
    return bool(op.get("deprecated", False))


def diff_deprecated_operations(old_spec: Dict[str, Any], new_spec: Dict[str, Any]) -> DiffReport:
    """Detect operations that became deprecated or had deprecation removed."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    old_ops = _get_operations(old_spec)
    new_ops = _get_operations(new_spec)

    changes = []

    for key, new_op in new_ops.items():
        path, method = key
        old_op = old_ops.get(key)
        if old_op is None:
            continue

        was_deprecated = _is_deprecated(old_op)
        now_deprecated = _is_deprecated(new_op)

        if not was_deprecated and now_deprecated:
            changes.append(Change(
                change_type=ChangeType.MODIFIED,
                severity=Severity.NON_BREAKING,
                path=path,
                operation=method.upper(),
                description=f"Operation {method.upper()} {path} marked as deprecated.",
            ))
        elif was_deprecated and not now_deprecated:
            changes.append(Change(
                change_type=ChangeType.MODIFIED,
                severity=Severity.NON_BREAKING,
                path=path,
                operation=method.upper(),
                description=f"Operation {method.upper()} {path} deprecation removed.",
            ))

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
