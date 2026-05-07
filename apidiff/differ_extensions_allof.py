"""Detect breaking changes in allOf / anyOf / oneOf schema compositions."""
from __future__ import annotations

from typing import Any

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_schemas(spec: dict[str, Any]) -> dict[str, Any]:
    return spec.get("components", {}).get("schemas", {})


def _collect_composition(schema: dict[str, Any], keyword: str) -> list[dict]:
    return schema.get(keyword, [])


def _schema_signature(schema: dict[str, Any]) -> str:
    """Return a stable string key for a sub-schema (best-effort)."""
    if "$ref" in schema:
        return schema["$ref"]
    if "type" in schema:
        return f"type:{schema['type']}"
    return str(sorted(schema.keys()))


def _diff_composition(
    schema_name: str,
    keyword: str,
    old_list: list[dict],
    new_list: list[dict],
    old_version: str,
    new_version: str,
) -> list[Change]:
    changes: list[Change] = []
    old_sigs = {_schema_signature(s) for s in old_list}
    new_sigs = {_schema_signature(s) for s in new_list}

    for sig in old_sigs - new_sigs:
        # Removing a member from allOf / oneOf / anyOf is breaking —
        # it narrows or changes the accepted contract.
        changes.append(
            Change(
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                path=f"#/components/schemas/{schema_name}/{keyword}",
                old_value=sig,
                new_value=None,
                description=(
                    f"Schema '{schema_name}': removed member from '{keyword}': {sig}"
                ),
            )
        )

    for sig in new_sigs - old_sigs:
        # Adding a member to allOf is breaking (stricter constraint);
        # adding to anyOf / oneOf is non-breaking (more permissive).
        severity = (
            Severity.BREAKING if keyword == "allOf" else Severity.NON_BREAKING
        )
        changes.append(
            Change(
                change_type=ChangeType.ADDED,
                severity=severity,
                path=f"#/components/schemas/{schema_name}/{keyword}",
                old_value=None,
                new_value=sig,
                description=(
                    f"Schema '{schema_name}': added member to '{keyword}': {sig}"
                ),
            )
        )

    return changes


def diff_allof(
    old_spec: dict[str, Any],
    new_spec: dict[str, Any],
) -> DiffReport:
    """Compare allOf / anyOf / oneOf compositions between two specs."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    old_schemas = _get_schemas(old_spec)
    new_schemas = _get_schemas(new_spec)

    changes: list[Change] = []
    keywords = ("allOf", "anyOf", "oneOf")

    for schema_name, old_schema in old_schemas.items():
        new_schema = new_schemas.get(schema_name, {})
        for kw in keywords:
            old_list = _collect_composition(old_schema, kw)
            new_list = _collect_composition(new_schema, kw)
            if not old_list and not new_list:
                continue
            changes.extend(
                _diff_composition(
                    schema_name, kw, old_list, new_list, old_version, new_version
                )
            )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
