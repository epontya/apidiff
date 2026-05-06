"""Diff component schemas between two OpenAPI specs."""

from __future__ import annotations

from typing import Any

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_schemas(spec: dict[str, Any]) -> dict[str, Any]:
    """Extract named schemas from components/schemas."""
    return spec.get("components", {}).get("schemas", {})


def _schema_type(schema: dict[str, Any]) -> str | None:
    return schema.get("type")


def _schema_nullable(schema: dict[str, Any]) -> bool:
    return schema.get("nullable", False)


def _schema_required(schema: dict[str, Any]) -> list[str]:
    return schema.get("required", [])


def diff_component_schemas(old_spec: dict[str, Any], new_spec: dict[str, Any]) -> DiffReport:
    """Compare component schemas between two specs and return a DiffReport."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    old_schemas = _get_schemas(old_spec)
    new_schemas = _get_schemas(new_spec)

    changes: list[Change] = []

    for name, old_schema in old_schemas.items():
        path = f"#/components/schemas/{name}"
        if name not in new_schemas:
            changes.append(
                Change(
                    change_type=ChangeType.REMOVED,
                    severity=Severity.BREAKING,
                    path=path,
                    operation=None,
                    description=f"Schema '{name}' was removed.",
                )
            )
            continue

        new_schema = new_schemas[name]

        old_type = _schema_type(old_schema)
        new_type = _schema_type(new_schema)
        if old_type != new_type:
            changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    severity=Severity.BREAKING,
                    path=path,
                    operation=None,
                    description=(
                        f"Schema '{name}' type changed from '{old_type}' to '{new_type}'."
                    ),
                )
            )

        old_nullable = _schema_nullable(old_schema)
        new_nullable = _schema_nullable(new_schema)
        if old_nullable and not new_nullable:
            changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    severity=Severity.BREAKING,
                    path=path,
                    operation=None,
                    description=f"Schema '{name}' is no longer nullable.",
                )
            )

        old_required = set(_schema_required(old_schema))
        new_required = set(_schema_required(new_schema))
        for field in new_required - old_required:
            changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    severity=Severity.BREAKING,
                    path=path,
                    operation=None,
                    description=(
                        f"Schema '{name}' added required field '{field}'."
                    ),
                )
            )

    for name in new_schemas:
        if name not in old_schemas:
            path = f"#/components/schemas/{name}"
            changes.append(
                Change(
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    path=path,
                    operation=None,
                    description=f"Schema '{name}' was added.",
                )
            )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
