"""Lint an OpenAPI diff report for common quality issues."""

from dataclasses import dataclass, field
from typing import List

from apidiff.differ import DiffReport, Severity


@dataclass
class LintIssue:
    code: str
    message: str
    severity: str  # "warning" | "error"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    def __bool__(self) -> bool:
        return not self.has_errors()


def lint_report(report: DiffReport) -> LintResult:
    """Run all lint checks against a DiffReport and return a LintResult."""
    result = LintResult()
    _check_undescribed_breaking_changes(report, result)
    _check_unknown_severity(report, result)
    _check_duplicate_changes(report, result)
    return result


def _check_undescribed_breaking_changes(report: DiffReport, result: LintResult) -> None:
    for change in report.changes:
        if change.severity == Severity.BREAKING and not change.description.strip():
            result.issues.append(
                LintIssue(
                    code="W001",
                    message=f"Breaking change at '{change.path}' [{change.operation}] has no description.",
                    severity="warning",
                )
            )


def _check_unknown_severity(report: DiffReport, result: LintResult) -> None:
    valid = {s.value for s in Severity}
    for change in report.changes:
        if change.severity.value not in valid:
            result.issues.append(
                LintIssue(
                    code="E001",
                    message=f"Change at '{change.path}' has unknown severity '{change.severity}'.",
                    severity="error",
                )
            )


def _check_duplicate_changes(report: DiffReport, result: LintResult) -> None:
    seen = set()
    for change in report.changes:
        key = (change.path, change.operation, change.change_type.value)
        if key in seen:
            result.issues.append(
                LintIssue(
                    code="W002",
                    message=f"Duplicate change detected at '{change.path}' [{change.operation}] type={change.change_type.value}.",
                    severity="warning",
                )
            )
        seen.add(key)
