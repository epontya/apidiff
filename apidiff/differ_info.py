"""Detects changes in the OpenAPI Info object between two specs."""

from apidiff.differ import Change, ChangeType, DiffReport, Severity

_INFO_FIELDS = {
    "title": (Severity.NON_BREAKING, "API title changed"),
    "version": (Severity.NON_BREAKING, "API version changed"),
    "description": (Severity.NON_BREAKING, "API description changed"),
    "termsOfService": (Severity.NON_BREAKING, "Terms of service URL changed"),
    "contact": (Severity.NON_BREAKING, "Contact information changed"),
    "license": (Severity.NON_BREAKING, "License information changed"),
}


def _get_info(spec: dict) -> dict:
    return spec.get("info", {})


def _field_changed(old_val, new_val) -> bool:
    return old_val != new_val


def diff_info(old_spec: dict, new_spec: dict) -> DiffReport:
    """Compare the info objects of two OpenAPI specs and return a DiffReport."""
    old_version = _get_info(old_spec).get("version", "unknown")
    new_version = _get_info(new_spec).get("version", "unknown")

    report = DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=[],
    )

    old_info = _get_info(old_spec)
    new_info = _get_info(new_spec)

    all_keys = set(old_info.keys()) | set(new_info.keys())

    for field in all_keys:
        old_val = old_info.get(field)
        new_val = new_info.get(field)

        if not _field_changed(old_val, new_val):
            continue

        severity, description_template = _INFO_FIELDS.get(
            field, (Severity.NON_BREAKING, f"Info field '{field}' changed")
        )

        if old_val is not None and new_val is None:
            change_type = ChangeType.REMOVED
            description = f"Info field '{field}' removed (was: {old_val!r})"
        elif old_val is None and new_val is not None:
            change_type = ChangeType.ADDED
            description = f"Info field '{field}' added (now: {new_val!r})"
        else:
            change_type = ChangeType.MODIFIED
            description = f"{description_template}: {old_val!r} -> {new_val!r}"

        report.changes.append(
            Change(
                change_type=change_type,
                severity=severity,
                path=f"info.{field}",
                operation=None,
                description=description,
            )
        )

    return report
