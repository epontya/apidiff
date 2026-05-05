"""Detect changes in OpenAPI example values across spec versions."""

from __future__ import annotations

from typing import Any

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_examples(spec: dict[str, Any]) -> dict[str, Any]:
    """Extract top-level named examples from components."""
    return spec.get("components", {}).get("examples", {})


def _get_inline_examples(spec: dict[str, Any]) -> dict[str, Any]:
    """Collect inline examples from path operation request/response bodies."""
    inline: dict[str, Any] = {}
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            # request body examples
            for media_type, media_obj in (
                operation.get("requestBody", {})
                .get("content", {})
                .items()
            ):
                for ex_name, ex_val in media_obj.get("examples", {}).items():
                    key = f"{path}:{method}:requestBody:{media_type}:{ex_name}"
                    inline[key] = ex_val
            # response examples
            for status, response in operation.get("responses", {}).items():
                for media_type, media_obj in response.get("content", {}).items():
                    for ex_name, ex_val in media_obj.get("examples", {}).items():
                        key = f"{path}:{method}:response:{status}:{media_type}:{ex_name}"
                        inline[key] = ex_val
    return inline


def diff_examples(old_spec: dict[str, Any], new_spec: dict[str, Any]) -> DiffReport:
    """Compare example objects between two OpenAPI specs.

    Removal of a named example is non-breaking (documentation only).
    Addition of a named example is non-breaking.
    Value changes are non-breaking (examples are informational).
    """
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    changes: list[Change] = []

    old_named = _get_examples(old_spec)
    new_named = _get_examples(new_spec)

    for name in old_named:
        if name not in new_named:
            changes.append(
                Change(
                    change_type=ChangeType.REMOVED,
                    severity=Severity.NON_BREAKING,
                    path=f"#/components/examples/{name}",
                    operation=None,
                    description=f"Example '{name}' removed from components.",
                )
            )
        elif old_named[name] != new_named[name]:
            changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    severity=Severity.NON_BREAKING,
                    path=f"#/components/examples/{name}",
                    operation=None,
                    description=f"Example '{name}' value changed.",
                )
            )

    for name in new_named:
        if name not in old_named:
            changes.append(
                Change(
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    path=f"#/components/examples/{name}",
                    operation=None,
                    description=f"Example '{name}' added to components.",
                )
            )

    old_inline = _get_inline_examples(old_spec)
    new_inline = _get_inline_examples(new_spec)

    for key in old_inline:
        if key not in new_inline:
            changes.append(
                Change(
                    change_type=ChangeType.REMOVED,
                    severity=Severity.NON_BREAKING,
                    path=key,
                    operation=None,
                    description=f"Inline example '{key}' removed.",
                )
            )
        elif old_inline[key] != new_inline[key]:
            changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    severity=Severity.NON_BREAKING,
                    path=key,
                    operation=None,
                    description=f"Inline example '{key}' value changed.",
                )
            )

    for key in new_inline:
        if key not in old_inline:
            changes.append(
                Change(
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    path=key,
                    operation=None,
                    description=f"Inline example '{key}' added.",
                )
            )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
