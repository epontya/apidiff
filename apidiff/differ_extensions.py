"""Extension to differ.py: detects changes in request/response body schemas."""

from typing import List
from apidiff.differ import Change, ChangeType, Severity, DiffReport


def _get_request_body_schema(operation: dict) -> dict:
    """Extract the JSON schema from a requestBody, if present."""
    try:
        return (
            operation
            .get("requestBody", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
        )
    except AttributeError:
        return {}


def _get_response_schema(operation: dict, status_code: str = "200") -> dict:
    """Extract the JSON schema from a response, if present."""
    try:
        return (
            operation
            .get("responses", {})
            .get(status_code, {})
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
        )
    except AttributeError:
        return {}


def _diff_schema_type(path: str, operation: str, location: str,
                      old_schema: dict, new_schema: dict) -> List[Change]:
    """Detect type changes in a schema (breaking)."""
    changes: List[Change] = []
    old_type = old_schema.get("type")
    new_type = new_schema.get("type")
    if old_type and new_type and old_type != new_type:
        changes.append(Change(
            change_type=ChangeType.MODIFIED,
            severity=Severity.BREAKING,
            path=path,
            operation=operation,
            description=(
                f"{location} schema type changed from '{old_type}' to '{new_type}'"
            ),
        ))
    return changes


def diff_request_response_schemas(
    old_spec: dict, new_spec: dict, old_version: str, new_version: str
) -> DiffReport:
    """Compare request body and response schemas across all paths/operations."""
    changes: List[Change] = []
    old_paths = old_spec.get("paths", {})
    new_paths = new_spec.get("paths", {})

    for path, old_ops in old_paths.items():
        new_ops = new_paths.get(path, {})
        if not isinstance(old_ops, dict) or not isinstance(new_ops, dict):
            continue
        for method in ("get", "post", "put", "patch", "delete"):
            old_op = old_ops.get(method)
            new_op = new_ops.get(method)
            if not old_op or not new_op:
                continue

            # Request body schema type diff
            old_req = _get_request_body_schema(old_op)
            new_req = _get_request_body_schema(new_op)
            if old_req and new_req:
                changes.extend(
                    _diff_schema_type(path, method.upper(), "request body", old_req, new_req)
                )

            # Response 200 schema type diff
            old_res = _get_response_schema(old_op)
            new_res = _get_response_schema(new_op)
            if old_res and new_res:
                changes.extend(
                    _diff_schema_type(path, method.upper(), "response 200", old_res, new_res)
                )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
