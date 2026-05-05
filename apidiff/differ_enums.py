"""Detect breaking and non-breaking changes to enum values in request/response schemas."""

from typing import Any

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_enum_values(schema: dict) -> set:
    """Return the set of enum values from a schema, or empty set if none."""
    return set(schema.get("enum") or [])


def _collect_schemas(spec: dict) -> dict[str, dict]:
    """Collect all named schemas from components/definitions."""
    components = spec.get("components", {})
    schemas = components.get("schemas", {})
    # Also support Swagger 2.0 definitions
    definitions = spec.get("definitions", {})
    return {**definitions, **schemas}


def _collect_inline_enums(spec: dict) -> dict[str, dict]:
    """Walk paths and collect inline enum schemas keyed by a descriptive path."""
    found: dict[str, dict] = {}
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            # Request body
            for media_type, media_obj in (
                operation.get("requestBody", {})
                .get("content", {})
                .items()
            ):
                schema = media_obj.get("schema", {})
                if "enum" in schema:
                    key = f"{path}:{method}:requestBody:{media_type}"
                    found[key] = schema
            # Responses
            for status, response in operation.get("responses", {}).items():
                for media_type, media_obj in (
                    response.get("content", {}).items()
                ):
                    schema = media_obj.get("schema", {})
                    if "enum" in schema:
                        key = f"{path}:{method}:response:{status}:{media_type}"
                        found[key] = schema
    return found


def diff_enums(old_spec: dict, new_spec: dict) -> DiffReport:
    """Compare enum values between two specs and return a DiffReport."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    changes: list[Change] = []

    old_schemas = _collect_schemas(old_spec)
    new_schemas = _collect_schemas(new_spec)

    all_keys = set(old_schemas) | set(new_schemas)
    for name in all_keys:
        old_vals = _get_enum_values(old_schemas.get(name, {}))
        new_vals = _get_enum_values(new_schemas.get(name, {}))
        if old_vals == new_vals:
            continue
        for removed in old_vals - new_vals:
            changes.append(
                Change(
                    change_type=ChangeType.REMOVED,
                    severity=Severity.BREAKING,
                    path=f"#/components/schemas/{name}",
                    description=f"Enum value '{removed}' removed from schema '{name}'",
                )
            )
        for added in new_vals - old_vals:
            changes.append(
                Change(
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    path=f"#/components/schemas/{name}",
                    description=f"Enum value '{added}' added to schema '{name}'",
                )
            )

    old_inline = _collect_inline_enums(old_spec)
    new_inline = _collect_inline_enums(new_spec)

    all_inline_keys = set(old_inline) | set(new_inline)
    for key in all_inline_keys:
        old_vals = _get_enum_values(old_inline.get(key, {}))
        new_vals = _get_enum_values(new_inline.get(key, {}))
        if old_vals == new_vals:
            continue
        for removed in old_vals - new_vals:
            changes.append(
                Change(
                    change_type=ChangeType.REMOVED,
                    severity=Severity.BREAKING,
                    path=key,
                    description=f"Enum value '{removed}' removed from inline schema at '{key}'",
                )
            )
        for added in new_vals - old_vals:
            changes.append(
                Change(
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    path=key,
                    description=f"Enum value '{added}' added to inline schema at '{key}'",
                )
            )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
