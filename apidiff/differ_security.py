"""Detects breaking and non-breaking changes in OpenAPI security schemes."""

from typing import Any
from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_security_schemes(spec: dict) -> dict:
    """Extract security schemes from components."""
    return spec.get("components", {}).get("securitySchemes", {})


def _get_global_security(spec: dict) -> list:
    """Extract top-level security requirements."""
    return spec.get("security", [])


def _security_req_to_set(requirements: list) -> set:
    """Flatten a list of security requirement objects into a set of scheme names."""
    names = set()
    for req in requirements:
        names.update(req.keys())
    return names


def diff_security(old_spec: dict, new_spec: dict) -> DiffReport:
    """Compare security schemes and global security requirements between two specs."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")
    changes: list[Change] = []

    old_schemes = _get_security_schemes(old_spec)
    new_schemes = _get_security_schemes(new_spec)

    # Removed security schemes — breaking
    for name in old_schemes:
        if name not in new_schemes:
            changes.append(Change(
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                path=f"#/components/securitySchemes/{name}",
                operation=None,
                description=f"Security scheme '{name}' was removed.",
            ))

    # Added security schemes — non-breaking
    for name in new_schemes:
        if name not in old_schemes:
            changes.append(Change(
                change_type=ChangeType.ADDED,
                severity=Severity.NON_BREAKING,
                path=f"#/components/securitySchemes/{name}",
                operation=None,
                description=f"Security scheme '{name}' was added.",
            ))

    # Changed scheme type — breaking
    for name in old_schemes:
        if name in new_schemes:
            old_type = old_schemes[name].get("type")
            new_type = new_schemes[name].get("type")
            if old_type != new_type:
                changes.append(Change(
                    change_type=ChangeType.MODIFIED,
                    severity=Severity.BREAKING,
                    path=f"#/components/securitySchemes/{name}/type",
                    operation=None,
                    description=(
                        f"Security scheme '{name}' type changed "
                        f"from '{old_type}' to '{new_type}'."
                    ),
                ))

    # Global security requirements changes
    old_global = _security_req_to_set(_get_global_security(old_spec))
    new_global = _security_req_to_set(_get_global_security(new_spec))

    for name in old_global - new_global:
        changes.append(Change(
            change_type=ChangeType.REMOVED,
            severity=Severity.BREAKING,
            path="#/security",
            operation=None,
            description=f"Global security requirement '{name}' was removed.",
        ))

    for name in new_global - old_global:
        changes.append(Change(
            change_type=ChangeType.ADDED,
            severity=Severity.NON_BREAKING,
            path="#/security",
            operation=None,
            description=f"Global security requirement '{name}' was added.",
        ))

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
