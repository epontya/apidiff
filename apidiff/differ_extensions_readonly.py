"""Detect changes to readOnly/writeOnly flags on schema properties."""

from apidiff.differ import ChangeType, Severity, Change, DiffReport


def _get_schemas(spec: dict) -> dict:
    return spec.get("components", {}).get("schemas", {})


def _get_properties(schema: dict) -> dict:
    return schema.get("properties", {})


def _get_flag(prop: dict, flag: str) -> bool:
    return bool(prop.get(flag, False))


def _is_breaking_flag_change(flag: str, old_val: bool, new_val: bool) -> bool:
    """readOnly: adding is breaking (clients may have been writing).
       writeOnly: adding is breaking (clients may have been reading).
       Removing either flag is non-breaking.
    """
    return (not old_val) and new_val


def diff_readonly(
    old_spec: dict,
    new_spec: dict,
    old_version: str = "old",
    new_version: str = "new",
) -> DiffReport:
    changes: list[Change] = []
    old_schemas = _get_schemas(old_spec)
    new_schemas = _get_schemas(new_spec)

    for schema_name, old_schema in old_schemas.items():
        new_schema = new_schemas.get(schema_name, {})
        old_props = _get_properties(old_schema)
        new_props = _get_properties(new_schema)

        for prop_name, old_prop in old_props.items():
            new_prop = new_props.get(prop_name, {})

            for flag in ("readOnly", "writeOnly"):
                old_val = _get_flag(old_prop, flag)
                new_val = _get_flag(new_prop, flag)

                if old_val == new_val:
                    continue

                breaking = _is_breaking_flag_change(flag, old_val, new_val)
                path = f"#/components/schemas/{schema_name}/properties/{prop_name}/{flag}"
                description = (
                    f"Property '{prop_name}' in schema '{schema_name}': "
                    f"{flag} changed from {old_val} to {new_val}"
                )
                changes.append(
                    Change(
                        path=path,
                        operation=None,
                        change_type=ChangeType.MODIFIED,
                        severity=Severity.BREAKING if breaking else Severity.NON_BREAKING,
                        description=description,
                    )
                )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
