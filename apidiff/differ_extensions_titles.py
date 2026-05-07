"""Diff schema and property title changes between two OpenAPI specs."""

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_schemas(spec: dict) -> dict:
    return spec.get("components", {}).get("schemas", {})


def _get_properties(schema: dict) -> dict:
    return schema.get("properties", {})


def _get_title(obj: dict) -> str | None:
    return obj.get("title")


def diff_titles(old_spec: dict, new_spec: dict) -> DiffReport:
    """Detect title changes on schemas and their properties.

    Removing or changing a title is non-breaking (documentation only).
    Adding a title is also non-breaking.
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

        # Check top-level schema title
        old_title = _get_title(old_schema)
        new_title = _get_title(new_schema)

        if old_title != new_title:
            if old_title is None:
                change_type = ChangeType.ADDED
            elif new_title is None:
                change_type = ChangeType.REMOVED
            else:
                change_type = ChangeType.MODIFIED

            changes.append(
                Change(
                    path=f"#/components/schemas/{schema_name}",
                    change_type=change_type,
                    severity=Severity.NON_BREAKING,
                    description=(
                        f"Schema '{schema_name}' title changed: "
                        f"{old_title!r} -> {new_title!r}"
                    ),
                )
            )

        # Check property titles
        old_props = _get_properties(old_schema)
        new_props = _get_properties(new_schema)
        all_props = set(old_props) | set(new_props)

        for prop_name in sorted(all_props):
            old_prop_title = _get_title(old_props.get(prop_name, {}))
            new_prop_title = _get_title(new_props.get(prop_name, {}))

            if old_prop_title != new_prop_title:
                if old_prop_title is None:
                    change_type = ChangeType.ADDED
                elif new_prop_title is None:
                    change_type = ChangeType.REMOVED
                else:
                    change_type = ChangeType.MODIFIED

                changes.append(
                    Change(
                        path=f"#/components/schemas/{schema_name}/properties/{prop_name}",
                        change_type=change_type,
                        severity=Severity.NON_BREAKING,
                        description=(
                            f"Property '{prop_name}' title changed on schema "
                            f"'{schema_name}': {old_prop_title!r} -> {new_prop_title!r}"
                        ),
                    )
                )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
