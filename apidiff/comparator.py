"""Schema-level field comparator for detecting structural changes in request/response bodies."""

from dataclasses import dataclass, field
from typing import Any

from apidiff.differ import Change, ChangeType, Severity


@dataclass
class FieldDiff:
    path: str
    field_name: str
    change_type: ChangeType
    severity: Severity
    old_value: Any = None
    new_value: Any = None

    def to_change(self, operation: str = "unknown", method: str = "unknown") -> Change:
        description = _describe_field_diff(self)
        return Change(
            change_type=self.change_type,
            severity=self.severity,
            path=self.path,
            operation=operation,
            description=description,
        )


def _describe_field_diff(diff: FieldDiff) -> str:
    if diff.change_type == ChangeType.REMOVED:
        return f"Field '{diff.field_name}' removed"
    if diff.change_type == ChangeType.ADDED:
        return f"Field '{diff.field_name}' added"
    return f"Field '{diff.field_name}' changed from '{diff.old_value}' to '{diff.new_value}'"


def compare_schemas(path: str, old_schema: dict, new_schema: dict) -> list[FieldDiff]:
    """Compare two JSON schemas and return a list of field-level diffs."""
    diffs: list[FieldDiff] = []
    old_props = old_schema.get("properties", {})
    new_props = new_schema.get("properties", {})
    old_required = set(old_schema.get("required", []))
    new_required = set(new_schema.get("required", []))

    for field_name in old_props:
        if field_name not in new_props:
            severity = Severity.BREAKING if field_name in old_required else Severity.NON_BREAKING
            diffs.append(FieldDiff(path, field_name, ChangeType.REMOVED, severity, old_props[field_name]))

    for field_name in new_props:
        if field_name not in old_props:
            severity = Severity.BREAKING if field_name in new_required else Severity.NON_BREAKING
            diffs.append(FieldDiff(path, field_name, ChangeType.ADDED, severity, new_value=new_props[field_name]))

    for field_name in old_props:
        if field_name in new_props:
            old_type = old_props[field_name].get("type")
            new_type = new_props[field_name].get("type")
            if old_type != new_type:
                diffs.append(FieldDiff(path, field_name, ChangeType.MODIFIED, Severity.BREAKING, old_type, new_type))

    return diffs
