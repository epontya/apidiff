"""Detect changes to default values in request/response schemas."""

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_schemas(spec: dict) -> dict:
    """Extract component schemas from a spec."""
    return spec.get("components", {}).get("schemas", {})


def _get_properties(schema: dict) -> dict:
    """Return properties dict from a schema."""
    return schema.get("properties", {})


def _get_default(prop: dict):
    """Return the default value for a property, or a sentinel if absent."""
    _MISSING = object
    return prop.get("default", _MISSING)


def diff_defaults(old_spec: dict, new_spec: dict) -> DiffReport:
    """Detect added, removed, or changed default values across component schemas."""
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
            old_prop = old_props.get(prop_name, {})
            new_prop = new_props.get(prop_name, {})

            _MISSING = "__missing__"
            old_default = old_prop.get("default", _MISSING)
            new_default = new_prop.get("default", _MISSING)

            if old_default == new_default:
                continue

            path = f"#/components/schemas/{schema_name}/properties/{prop_name}/default"

            if old_default == _MISSING:
                changes.append(Change(
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    path=path,
                    description=f"Default value added to '{prop_name}' in schema '{schema_name}': {new_default!r}",
                ))
            elif new_default == _MISSING:
                changes.append(Change(
                    change_type=ChangeType.REMOVED,
                    severity=Severity.BREAKING,
                    path=path,
                    description=f"Default value removed from '{prop_name}' in schema '{schema_name}' (was {old_default!r})",
                ))
            else:
                changes.append(Change(
                    change_type=ChangeType.MODIFIED,
                    severity=Severity.NON_BREAKING,
                    path=path,
                    description=(
                        f"Default value changed for '{prop_name}' in schema '{schema_name}': "
                        f"{old_default!r} -> {new_default!r}"
                    ),
                ))

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
