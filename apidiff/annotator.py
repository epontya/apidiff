"""Annotate diff report changes with human-readable migration hints."""

from dataclasses import dataclass, field
from typing import List, Optional

from apidiff.differ import Change, ChangeType, DiffReport, Severity


@dataclass
class AnnotatedChange:
    change: Change
    hint: str
    migration_effort: str  # "low", "medium", "high"


@dataclass
class AnnotatedReport:
    version_old: str
    version_new: str
    annotated: List[AnnotatedChange] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.annotated) == 0


_HINTS = {
    ChangeType.REMOVED_PATH: (
        "Remove all client calls to '{path}'. Update routing and client SDKs.",
        "high",
    ),
    ChangeType.REMOVED_OPERATION: (
        "Remove usage of '{method} {path}'. Check all consumers of this endpoint.",
        "high",
    ),
    ChangeType.REMOVED_PARAMETER: (
        "Parameter '{name}' on '{method} {path}' was removed. Update callers to omit it.",
        "medium",
    ),
    ChangeType.ADDED_REQUIRED_PARAMETER: (
        "New required parameter '{name}' added to '{method} {path}'. All callers must supply it.",
        "high",
    ),
    ChangeType.MODIFIED_RESPONSE_SCHEMA: (
        "Response schema changed for '{method} {path}'. Validate deserialization logic.",
        "medium",
    ),
    ChangeType.ADDED_PATH: (
        "New path '{path}' available. No action required for existing clients.",
        "low",
    ),
    ChangeType.ADDED_OPERATION: (
        "New operation '{method} {path}' available. Optionally adopt in clients.",
        "low",
    ),
}

_DEFAULT_HINT = ("Review change at '{path}' and update clients accordingly.", "medium")


def _build_hint(change: Change) -> tuple:
    template, effort = _HINTS.get(change.change_type, _DEFAULT_HINT)
    hint = template.format(
        path=change.path or "",
        method=(change.operation or "").upper(),
        name=change.details.get("name", "") if change.details else "",
    )
    return hint, effort


def annotate_report(report: DiffReport) -> AnnotatedReport:
    """Attach migration hints to every change in the report."""
    annotated = AnnotatedReport(
        version_old=report.version_old,
        version_new=report.version_new,
    )
    for change in report.changes:
        hint, effort = _build_hint(change)
        annotated.annotated.append(
            AnnotatedChange(change=change, hint=hint, migration_effort=effort)
        )
    return annotated
