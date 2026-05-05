"""Diff webhook definitions between two OpenAPI specs."""
from typing import Any
from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_webhooks(spec: dict[str, Any]) -> dict[str, Any]:
    """Extract webhooks from an OpenAPI 3.1 spec."""
    return spec.get("webhooks", {})


def _get_webhook_operations(webhook: dict[str, Any]) -> set[str]:
    http_methods = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
    return {k for k in webhook if k.lower() in http_methods}


def diff_webhooks(old_spec: dict[str, Any], new_spec: dict[str, Any]) -> DiffReport:
    """Compare webhook definitions and return a DiffReport."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    old_webhooks = _get_webhooks(old_spec)
    new_webhooks = _get_webhooks(new_spec)

    changes: list[Change] = []

    for name in old_webhooks:
        if name not in new_webhooks:
            changes.append(Change(
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                path=f"webhooks/{name}",
                description=f"Webhook '{name}' was removed.",
            ))
            continue

        old_ops = _get_webhook_operations(old_webhooks[name])
        new_ops = _get_webhook_operations(new_webhooks[name])

        for op in old_ops - new_ops:
            changes.append(Change(
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                path=f"webhooks/{name}/{op}",
                description=f"Operation '{op}' removed from webhook '{name}'.",
            ))

        for op in new_ops - old_ops:
            changes.append(Change(
                change_type=ChangeType.ADDED,
                severity=Severity.NON_BREAKING,
                path=f"webhooks/{name}/{op}",
                description=f"Operation '{op}' added to webhook '{name}'.",
            ))

    for name in new_webhooks:
        if name not in old_webhooks:
            changes.append(Change(
                change_type=ChangeType.ADDED,
                severity=Severity.NON_BREAKING,
                path=f"webhooks/{name}",
                description=f"Webhook '{name}' was added.",
            ))

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
