"""Detect changes to schema property constraints (min/max, minLength/maxLength, etc.)."""
from typing import Any
from apidiff.differ import Change, ChangeType, DiffReport, Severity

_CONSTRAINT_FIELDS = [
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "minLength", "maxLength", "minItems", "maxItems",
    "minProperties", "maxProperties",
]


def _get_schemas(spec: dict) -> dict:
    return spec.get("components", {}).get("schemas", {})


def _get_properties(schema: dict) -> dict:
    return schema.get("properties", {})


def _get_constraint(prop: dict, field: str) -> Any:
    return prop.get(field)


def _is_tightening(field: str, old_val: Any, new_val: Any) -> bool:
    """Return True if the constraint change is more restrictive."""
    if field in ("minimum", "exclusiveMinimum", "minLength", "minItems", "minProperties"):
        return new_val > old_val
    if field in ("maximum", "exclusiveMaximum", "maxLength", "maxItems", "maxProperties"):
        return new_val < old_val
    return False


def diff_constraints(old_spec: dict, new_spec: dict) -> DiffReport:
    """Compare schema property constraints between two specs."""
    changes: list[Change] = []
    old_schemas = _get_schemas(old_spec)
    new_schemas = _get_schemas(new_spec)

    for schema_name, old_schema in old_schemas.items():
        if schema_name not in new_schemas:
            continue
        new_schema = new_schemas[schema_name]
        old_props = _get_properties(old_schema)
        new_props = _get_properties(new_schema)

        for prop_name, old_prop in old_props.items():
            if prop_name not in new_props:
                continue
            new_prop = new_props[prop_name]
            for field in _CONSTRAINT_FIELDS:
                old_val = _get_constraint(old_prop, field)
                new_val = _get_constraint(new_prop, field)
                if old_val == new_val:
                    continue
                path = f"#/components/schemas/{schema_name}/properties/{prop_name}/{field}"
                if new_val is None:
                    change_type = ChangeType.REMOVED
                    severity = Severity.NON_BREAKING
                elif old_val is None:
                    change_type = ChangeType.ADDED
                    severity = Severity.BREAKING if _is_tightening(field, 0, new_val) else Severity.NON_BREAKING
                else:
                    change_type = ChangeType.MODIFIED
                    severity = Severity.BREAKING if _is_tightening(field, old_val, new_val) else Severity.NON_BREAKING
                changes.append(Change(
                    change_type=change_type,
                    severity=severity,
                    path=path,
                    description=f"Constraint '{field}' on '{schema_name}.{prop_name}' changed from {old_val!r} to {new_val!r}.",
                ))

    return DiffReport(
        old_version=old_spec.get("info", {}).get("version", "unknown"),
        new_version=new_spec.get("info", {}).get("version", "unknown"),
        changes=changes,
    )
