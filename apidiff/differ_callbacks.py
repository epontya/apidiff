"""Diff OpenAPI callback objects between two spec versions."""

from typing import Any

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_callbacks(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Collect all callbacks from paths/operations in the spec."""
    callbacks: dict[str, dict[str, Any]] = {}
    paths = spec.get("paths", {})
    for path, path_item in paths.items():
        for method in ("get", "post", "put", "patch", "delete", "options", "head", "trace"):
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue
            for cb_name, cb_obj in operation.get("callbacks", {}).items():
                key = f"{path}:{method}:{cb_name}"
                callbacks[key] = cb_obj
    return callbacks


def _get_callback_expressions(cb_obj: dict[str, Any]) -> set[str]:
    """Return the set of URL expression keys defined in a callback object."""
    return set(cb_obj.keys()) if isinstance(cb_obj, dict) else set()


def diff_callbacks(old_spec: dict[str, Any], new_spec: dict[str, Any]) -> DiffReport:
    """Compare callback definitions between two OpenAPI specs.

    Removing a callback is considered breaking (consumers rely on receiving events).
    Adding a callback is non-breaking.
    Removing a URL expression from an existing callback is breaking.
    Adding a URL expression is non-breaking.
    """
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    old_callbacks = _get_callbacks(old_spec)
    new_callbacks = _get_callbacks(new_spec)

    changes: list[Change] = []

    # Detect removed callbacks
    for key in old_callbacks:
        if key not in new_callbacks:
            changes.append(
                Change(
                    change_type=ChangeType.REMOVED,
                    severity=Severity.BREAKING,
                    path=key,
                    description=f"Callback '{key}' was removed.",
                )
            )
            continue

        # Detect removed / added URL expressions within existing callbacks
        old_exprs = _get_callback_expressions(old_callbacks[key])
        new_exprs = _get_callback_expressions(new_callbacks[key])

        for expr in old_exprs - new_exprs:
            changes.append(
                Change(
                    change_type=ChangeType.REMOVED,
                    severity=Severity.BREAKING,
                    path=f"{key}:{expr}",
                    description=f"Callback expression '{expr}' removed from '{key}'.",
                )
            )

        for expr in new_exprs - old_exprs:
            changes.append(
                Change(
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    path=f"{key}:{expr}",
                    description=f"Callback expression '{expr}' added to '{key}'.",
                )
            )

    # Detect added callbacks
    for key in new_callbacks:
        if key not in old_callbacks:
            changes.append(
                Change(
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    path=key,
                    description=f"Callback '{key}' was added.",
                )
            )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
