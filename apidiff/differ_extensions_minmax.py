"""Detects breaking changes in minimum/maximum value constraints on schema properties."""

from apidiff.differ import ChangeType, Severity, Change, DiffReport


def _get_schemas(spec: dict) -> dict:
    return spec.get("components", {}).get("schemas", {})


def _get_properties(schema: dict) -> dict:
    return schema.get("properties", {})


def _get_bounds(prop: dict) -> dict:
    return {
        "minimum": prop.get("minimum"),
        "maximum": prop.get("maximum"),
        "exclusiveMinimum": prop.get("exclusiveMinimum"),
        "exclusiveMaximum": prop.get("exclusiveMaximum"),
    }


def _is_tightening_min(old_val, new_val) -> bool:
    """Raising minimum is a tightening (breaking) change."""
    if old_val is None and new_val is not None:
        return True
    if old_val is not None and new_val is not None and new_val > old_val:
        return True
    return False


def _is_tightening_max(old_val, new_val) -> bool:
    """Lowering maximum is a tightening (breaking) change."""
    if old_val is None and new_val is not None:
        return True
    if old_val is not None and new_val is not None and new_val < old_val:
        return True
    return False


def diff_minmax(old_spec: dict, new_spec: dict) -> DiffReport:
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")
    changes: list[Change] = []

    old_schemas = _get_schemas(old_spec)
    new_schemas = _get_schemas(new_spec)

    for schema_name, old_schema in old_schemas.items():
        new_schema = new_schemas.get(schema_name, {})
        old_props = _get_properties(old_schema)
        new_props = _get_properties(new_schema)

        for prop_name, old_prop in old_props.items():
            new_prop = new_props.get(prop_name, {})
            old_bounds = _get_bounds(old_prop)
            new_bounds = _get_bounds(new_prop)

            for key in ("minimum", "exclusiveMinimum"):
                if _is_tightening_min(old_bounds[key], new_bounds[key]):
                    changes.append(Change(
                        change_type=ChangeType.MODIFIED,
                        severity=Severity.BREAKING,
                        path=f"#/components/schemas/{schema_name}/properties/{prop_name}",
                        description=f"Property '{prop_name}' {key} tightened from {old_bounds[key]} to {new_bounds[key]}",
                    ))
                elif old_bounds[key] is not None and (new_bounds[key] is None or new_bounds[key] < old_bounds[key]):
                    changes.append(Change(
                        change_type=ChangeType.MODIFIED,
                        severity=Severity.NON_BREAKING,
                        path=f"#/components/schemas/{schema_name}/properties/{prop_name}",
                        description=f"Property '{prop_name}' {key} loosened from {old_bounds[key]} to {new_bounds[key]}",
                    ))

            for key in ("maximum", "exclusiveMaximum"):
                if _is_tightening_max(old_bounds[key], new_bounds[key]):
                    changes.append(Change(
                        change_type=ChangeType.MODIFIED,
                        severity=Severity.BREAKING,
                        path=f"#/components/schemas/{schema_name}/properties/{prop_name}",
                        description=f"Property '{prop_name}' {key} tightened from {old_bounds[key]} to {new_bounds[key]}",
                    ))
                elif old_bounds[key] is not None and (new_bounds[key] is None or new_bounds[key] > old_bounds[key]):
                    changes.append(Change(
                        change_type=ChangeType.MODIFIED,
                        severity=Severity.NON_BREAKING,
                        path=f"#/components/schemas/{schema_name}/properties/{prop_name}",
                        description=f"Property '{prop_name}' {key} loosened from {old_bounds[key]} to {new_bounds[key]}",
                    ))

    return DiffReport(old_version=old_version, new_version=new_version, changes=changes)
