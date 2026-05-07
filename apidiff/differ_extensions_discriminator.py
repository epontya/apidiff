"""Diff discriminator mappings in OpenAPI component schemas."""
from __future__ import annotations

from typing import Any

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_schemas(spec: dict[str, Any]) -> dict[str, Any]:
    return spec.get("components", {}).get("schemas", {})


def _get_discriminator(schema: dict[str, Any]) -> dict[str, Any] | None:
    return schema.get("discriminator")


def _get_mapping(discriminator: dict[str, Any]) -> dict[str, str]:
    return discriminator.get("mapping", {})


def diff_discriminator(old_spec: dict[str, Any], new_spec: dict[str, Any]) -> DiffReport:
    """Detect breaking and non-breaking discriminator changes."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    changes: list[Change] = []
    old_schemas = _get_schemas(old_spec)
    new_schemas = _get_schemas(new_spec)

    for schema_name, old_schema in old_schemas.items():
        new_schema = new_schemas.get(schema_name, {})
        old_disc = _get_discriminator(old_schema)
        new_disc = _get_discriminator(new_schema)

        if old_disc is None and new_disc is None:
            continue

        path = f"#/components/schemas/{schema_name}/discriminator"

        # Discriminator removed entirely — breaking
        if old_disc is not None and new_disc is None:
            changes.append(Change(
                path=path,
                operation="N/A",
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                description=f"Discriminator removed from schema '{schema_name}'",
            ))
            continue

        # Discriminator added — non-breaking
        if old_disc is None and new_disc is not None:
            changes.append(Change(
                path=path,
                operation="N/A",
                change_type=ChangeType.ADDED,
                severity=Severity.NON_BREAKING,
                description=f"Discriminator added to schema '{schema_name}'",
            ))
            continue

        # propertyName changed — breaking
        old_prop = old_disc.get("propertyName")
        new_prop = new_disc.get("propertyName")
        if old_prop != new_prop:
            changes.append(Change(
                path=f"{path}/propertyName",
                operation="N/A",
                change_type=ChangeType.MODIFIED,
                severity=Severity.BREAKING,
                description=(
                    f"Discriminator propertyName changed in '{schema_name}': "
                    f"'{old_prop}' -> '{new_prop}'"
                ),
            ))

        # mapping entries removed — breaking
        old_mapping = _get_mapping(old_disc)
        new_mapping = _get_mapping(new_disc)
        for key, val in old_mapping.items():
            if key not in new_mapping:
                changes.append(Change(
                    path=f"{path}/mapping/{key}",
                    operation="N/A",
                    change_type=ChangeType.REMOVED,
                    severity=Severity.BREAKING,
                    description=f"Discriminator mapping key '{key}' removed from '{schema_name}'",
                ))
            elif new_mapping[key] != val:
                changes.append(Change(
                    path=f"{path}/mapping/{key}",
                    operation="N/A",
                    change_type=ChangeType.MODIFIED,
                    severity=Severity.BREAKING,
                    description=(
                        f"Discriminator mapping '{key}' changed in '{schema_name}': "
                        f"'{val}' -> '{new_mapping[key]}'"
                    ),
                ))

        # mapping entries added — non-breaking
        for key in new_mapping:
            if key not in old_mapping:
                changes.append(Change(
                    path=f"{path}/mapping/{key}",
                    operation="N/A",
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    description=f"Discriminator mapping key '{key}' added to '{schema_name}'",
                ))

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
