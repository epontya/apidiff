"""Generates patch suggestions to fix breaking changes in an OpenAPI spec."""

from dataclasses import dataclass, field
from typing import List, Optional

from apidiff.differ import ChangeType, DiffReport, Change


@dataclass
class PatchSuggestion:
    path: str
    operation: Optional[str]
    change_type: ChangeType
    description: str
    suggestion: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "operation": self.operation,
            "change_type": self.change_type.value,
            "description": self.description,
            "suggestion": self.suggestion,
        }


@dataclass
class PatchPlan:
    old_version: str
    new_version: str
    suggestions: List[PatchSuggestion] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.suggestions) == 0

    def to_dict(self) -> dict:
        return {
            "old_version": self.old_version,
            "new_version": self.new_version,
            "suggestions": [s.to_dict() for s in self.suggestions],
        }


_SUGGESTIONS = {
    ChangeType.REMOVED: "Restore the removed path/operation or provide a deprecated redirect before removal.",
    ChangeType.MODIFIED: "Ensure backward-compatible changes only; use versioning or additive fields instead.",
    ChangeType.ADDED: "No breaking change — no patch required for additions.",
}


def _suggest_for_change(change: Change) -> str:
    return _SUGGESTIONS.get(
        change.change_type,
        "Review the change and ensure clients are not adversely affected.",
    )


def build_patch_plan(report: DiffReport) -> PatchPlan:
    """Build a PatchPlan with suggestions for every breaking change in the report."""
    plan = PatchPlan(
        old_version=report.old_version,
        new_version=report.new_version,
    )
    for change in report.changes:
        if not change.breaking:
            continue
        suggestion = PatchSuggestion(
            path=change.path,
            operation=change.operation,
            change_type=change.change_type,
            description=change.description,
            suggestion=_suggest_for_change(change),
        )
        plan.suggestions.append(suggestion)
    return plan


def format_patch_plan(plan: PatchPlan) -> str:
    """Render the patch plan as a human-readable text block."""
    if plan.is_empty():
        return "No breaking changes detected. No patches required.\n"
    lines = [
        f"Patch Plan: {plan.old_version} -> {plan.new_version}",
        "=" * 50,
    ]
    for s in plan.suggestions:
        op = s.operation or "N/A"
        lines.append(f"\n[{s.change_type.value.upper()}] {s.path} ({op})")
        lines.append(f"  Issue      : {s.description}")
        lines.append(f"  Suggestion : {s.suggestion}")
    lines.append("")
    return "\n".join(lines)
