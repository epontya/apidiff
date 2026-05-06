"""Detect changes to field format constraints across component schemas."""

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_schemas(spec: dict) -> dict:
    return spec.get("components", {}).get("schemas", {})


def _get_properties(schema: dict) -> dict:
    return schema.get("properties", {})


def _get_format(prop: dict) -> str | None:
    return prop.get("format")


def diff_formats(old_spec: dict, new_spec: dict) -> DiffReport:
    """Compare property format constraints between two OpenAPI specs.

    Removing or changing a format is breaking (clients may rely on validation).
    Adding a format is non-breaking.
    """
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    changes: list[Change] = []

    old_schemas = _get_schemas(old_spec)
    new_schemas = _get_schemas(new_spec)

    for schema_name, old_schema in old_schemas.items():
        if schema_name not in new_schemas:
            continue  # schema removal handled elsewhere

        new_schema = new_schemas[schema_name]
        old_props = _get_properties(old_schema)
        new_props = _get_properties(new_schema)

        for prop_name, old_prop in old_props.items():
            if prop_name not in new_props:
                continue  # property removal handled elsewhere

            new_prop = new_props[prop_name]
            old_fmt = _get_format(old_prop)
            new_fmt = _get_format(new_prop)

            if old_fmt == new_fmt:
                continue

            path = f"#/components/schemas/{schema_name}/properties/{prop_name}/format"

            if old_fmt is not None and new_fmt is None:
                changes.append(
                    Change(
                        change_type=ChangeType.REMOVED,
                        severity=Severity.BREAKING,
                        path=path,
                        description=(
                            f"Format '{old_fmt}' removed from "
                            f"{schema_name}.{prop_name}"
                        ),
                    )
                )
            elif old_fmt is None and new_fmt is not None:
                changes.append(
                    Change(
                        change_type=ChangeType.ADDED,
                        severity=Severity.NON_BREAKING,
                        path=path,
                        description=(
                            f"Format '{new_fmt}' added to "
                            f"{schema_name}.{prop_name}"
                        ),
                    )
                )
            else:
                changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        severity=Severity.BREAKING,
                        path=path,
                        description=(
                            f"Format changed from '{old_fmt}' to '{new_fmt}' "
                            f"in {schema_name}.{prop_name}"
                        ),
                    )
                )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
