"""Generate migration hints from a diff report.

For each breaking change, produce a human-readable migration hint that
suggests what a consumer of the API must do to adapt.
"""

from dataclasses import dataclass, field
from typing import List

from apidiff.differ import Change, ChangeType, DiffReport, Severity


@dataclass
class MigrationHint:
    path: str
    operation: str
    change_type: str
    description: str
    suggestion: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "operation": self.operation,
            "change_type": self.change_type,
            "description": self.description,
            "suggestion": self.suggestion,
        }


@dataclass
class MigrationPlan:
    old_version: str
    new_version: str
    hints: List[MigrationHint] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.hints) == 0

    def to_dict(self) -> dict:
        return {
            "old_version": self.old_version,
            "new_version": self.new_version,
            "hints": [h.to_dict() for h in self.hints],
        }


_SUGGESTIONS = {
    ChangeType.REMOVED: "Remove all calls to this endpoint or update your client to use the replacement.",
    ChangeType.MODIFIED: "Review the changed field and update your request/response handling accordingly.",
    ChangeType.ADDED: "No action required; new functionality is available.",
}


def _suggestion_for(change: Change) -> str:
    return _SUGGESTIONS.get(
        change.change_type,
        "Review the API changelog and update your client as needed.",
    )


def build_migration_plan(report: DiffReport) -> MigrationPlan:
    """Return a MigrationPlan containing hints only for breaking changes."""
    plan = MigrationPlan(
        old_version=report.old_version,
        new_version=report.new_version,
    )
    for change in report.changes:
        if change.severity != Severity.BREAKING:
            continue
        hint = MigrationHint(
            path=change.path,
            operation=change.operation,
            change_type=change.change_type.value,
            description=change.description,
            suggestion=_suggestion_for(change),
        )
        plan.hints.append(hint)
    return plan


def format_migration_plan(plan: MigrationPlan) -> str:
    """Render a MigrationPlan as plain text."""
    lines = [
        f"Migration Plan: {plan.old_version} -> {plan.new_version}",
        "=" * 60,
    ]
    if plan.is_empty():
        lines.append("No breaking changes detected. No migration required.")
        return "\n".join(lines)
    for i, hint in enumerate(plan.hints, start=1):
        lines.append(f"\n[{i}] {hint.operation.upper()} {hint.path}")
        lines.append(f"    Change : {hint.change_type}")
        lines.append(f"    Detail : {hint.description}")
        lines.append(f"    Action : {hint.suggestion}")
    return "\n".join(lines)
