"""Diff pattern/regex constraints on schema properties between two OpenAPI specs."""

from __future__ import annotations

from typing import Any

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_schemas(spec: dict[str, Any]) -> dict[str, Any]:
    return spec.get("components", {}).get("schemas", {})


def _get_properties(schema: dict[str, Any]) -> dict[str, Any]:
    return schema.get("properties", {})


def _get_pattern(prop: dict[str, Any]) -> str | None:
    return prop.get("pattern")


def diff_patterns(old_spec: dict[str, Any], new_spec: dict[str, Any]) -> DiffReport:
    """Detect changes to pattern constraints on schema properties.

    Removing a pattern (less restrictive) is non-breaking.
    Adding or changing a pattern (more restrictive) is breaking.
    """
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    changes: list[Change] = []

    old_schemas = _get_schemas(old_spec)
    new_schemas = _get_schemas(new_spec)

    all_schema_names = set(old_schemas) | set(new_schemas)

    for schema_name in sorted(all_schema_names):
        old_schema = old_schemas.get(schema_name, {})
        new_schema = new_schemas.get(schema_name, {})

        old_props = _get_properties(old_schema)
        new_props = _get_properties(new_schema)

        all_props = set(old_props) | set(new_props)

        for prop_name in sorted(all_props):
            old_pattern = _get_pattern(old_props.get(prop_name, {}))
            new_pattern = _get_pattern(new_props.get(prop_name, {}))

            if old_pattern == new_pattern:
                continue

            path = f"#/components/schemas/{schema_name}/properties/{prop_name}/pattern"

            if old_pattern is not None and new_pattern is None:
                changes.append(Change(
                    change_type=ChangeType.REMOVED,
                    severity=Severity.NON_BREAKING,
                    path=path,
                    description=(
                        f"Pattern removed from '{schema_name}.{prop_name}' "
                        f"(was '{old_pattern}')"
                    ),
                ))
            elif old_pattern is None and new_pattern is not None:
                changes.append(Change(
                    change_type=ChangeType.ADDED,
                    severity=Severity.BREAKING,
                    path=path,
                    description=(
                        f"Pattern added to '{schema_name}.{prop_name}': '{new_pattern}'"
                    ),
                ))
            else:
                changes.append(Change(
                    change_type=ChangeType.MODIFIED,
                    severity=Severity.BREAKING,
                    path=path,
                    description=(
                        f"Pattern changed on '{schema_name}.{prop_name}': "
                        f"'{old_pattern}' -> '{new_pattern}'"
                    ),
                ))

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
