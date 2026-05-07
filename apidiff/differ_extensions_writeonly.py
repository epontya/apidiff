"""Detect changes to writeOnly flags on schema properties."""
from typing import Any, Dict, List

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_schemas(spec: Dict[str, Any]) -> Dict[str, Any]:
    return spec.get("components", {}).get("schemas", {})


def _get_properties(schema: Dict[str, Any]) -> Dict[str, Any]:
    return schema.get("properties", {})


def _get_flag(prop: Dict[str, Any]) -> bool:
    return bool(prop.get("writeOnly", False))


def _is_breaking_flag_change(old_flag: bool, new_flag: bool) -> bool:
    # Adding writeOnly to an existing property is breaking for writers;
    # removing it is non-breaking (property becomes readable again).
    return (not old_flag) and new_flag


def diff_writeonly(
    old_spec: Dict[str, Any],
    new_spec: Dict[str, Any],
) -> DiffReport:
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")
    changes: List[Change] = []

    old_schemas = _get_schemas(old_spec)
    new_schemas = _get_schemas(new_spec)

    for schema_name, old_schema in old_schemas.items():
        new_schema = new_schemas.get(schema_name, {})
        old_props = _get_properties(old_schema)
        new_props = _get_properties(new_schema)

        for prop_name, old_prop in old_props.items():
            new_prop = new_props.get(prop_name, {})
            old_flag = _get_flag(old_prop)
            new_flag = _get_flag(new_prop)

            if old_flag == new_flag:
                continue

            path = f"#/components/schemas/{schema_name}/properties/{prop_name}/writeOnly"
            breaking = _is_breaking_flag_change(old_flag, new_flag)
            changes.append(
                Change(
                    change_type=ChangeType.MODIFIED,
                    path=path,
                    severity=Severity.BREAKING if breaking else Severity.NON_BREAKING,
                    description=(
                        f"Property '{prop_name}' in schema '{schema_name}' "
                        f"writeOnly changed from {old_flag} to {new_flag}."
                    ),
                    old_value=str(old_flag),
                    new_value=str(new_flag),
                )
            )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
