"""Diff response codes between two OpenAPI specs."""

from __future__ import annotations

from typing import Any, Dict, List

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_responses(spec: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Collect all (path, method, status_code) -> response mappings."""
    result: Dict[str, Dict[str, Any]] = {}
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method not in ("get", "post", "put", "patch", "delete", "head", "options", "trace"):
                continue
            if not isinstance(operation, dict):
                continue
            for status_code, response in operation.get("responses", {}).items():
                key = f"{path}::{method.upper()}::{status_code}"
                result[key] = response
    return result


def _parse_key(key: str):
    parts = key.split("::")
    return parts[0], parts[1], parts[2]


def diff_response_codes(
    old_spec: Dict[str, Any],
    new_spec: Dict[str, Any],
) -> DiffReport:
    """Detect added and removed response status codes."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    old_responses = _get_responses(old_spec)
    new_responses = _get_responses(new_spec)

    changes: List[Change] = []

    for key in old_responses:
        if key not in new_responses:
            path, method, status_code = _parse_key(key)
            changes.append(
                Change(
                    change_type=ChangeType.REMOVED,
                    severity=Severity.BREAKING,
                    path=path,
                    operation=method,
                    description=f"Response status code '{status_code}' removed from {method} {path}",
                )
            )

    for key in new_responses:
        if key not in old_responses:
            path, method, status_code = _parse_key(key)
            changes.append(
                Change(
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    path=path,
                    operation=method,
                    description=f"Response status code '{status_code}' added to {method} {path}",
                )
            )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
