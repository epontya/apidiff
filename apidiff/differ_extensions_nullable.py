"""Detect changes to nullable flags on schema properties."""
from __future__ import annotations

from typing import Any

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_schemas(spec: dict[str, Any]) -> dict[str, Any]:
    return spec.get("components", {}).get("schemas", {})


def _get_properties(schema: dict[str, Any]) -> dict[str, Any]:
    return schema.get("properties", {})


def _is_nullable(prop: dict[str, Any]) -> bool:
    """Support both OAS 3.0 nullable:true and OAS 3.1 type arrays."""
    if prop.get("nullable", False):
        return True
    types = prop.get("type", [])
    if isinstance(types, list) and "null" in types:
        return True
    return False


def diff_nullable(
    old_spec: dict[str, Any],
    new_spec: dict[str, Any],
) -> DiffReport:
    """Return a DiffReport describing nullable flag changes on component schema properties."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    changes: list[Change] = []

    old_schemas = _get_schemas(old_spec)
    new_schemas = _get_schemas(new_spec)

    common_schemas = set(old_schemas) & set(new_schemas)

    for schema_name in sorted(common_schemas):
        old_props = _get_properties(old_schemas[schema_name])
        new_props = _get_properties(new_schemas[schema_name])
        common_props = set(old_props) & set(new_props)

        for prop_name in sorted(common_props):
            old_nullable = _is_nullable(old_props[prop_name])
            new_nullable = _is_nullable(new_props[prop_name])

            if old_nullable == new_nullable:
                continue

            path = f"#/components/schemas/{schema_name}/properties/{prop_name}"

            if old_nullable and not new_nullable:
                # Was nullable, no longer is — consumers relying on null values break
                changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        severity=Severity.BREAKING,
                        path=path,
                        description=(
                            f"Property '{prop_name}' in schema '{schema_name}' "
                            "is no longer nullable."
                        ),
                    )
                )
            else:
                # Became nullable — generally safe for existing consumers
                changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        severity=Severity.NON_BREAKING,
                        path=path,
                        description=(
                            f"Property '{prop_name}' in schema '{schema_name}' "
                            "is now nullable."
                        ),
                    )
                )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
