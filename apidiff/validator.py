"""Validates diff reports against configurable rule sets."""

from dataclasses import dataclass, field
from typing import List, Optional

from apidiff.differ import DiffReport, Severity, ChangeType


@dataclass
class ValidationRule:
    """A single validation rule applied to a diff report."""
    name: str
    description: str
    severity_threshold: Optional[Severity] = None
    forbidden_change_types: List[ChangeType] = field(default_factory=list)
    max_breaking_changes: Optional[int] = None


@dataclass
class ValidationResult:
    """Result of running validation rules against a report."""
    passed: bool
    violations: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.passed


def validate_report(report: DiffReport, rules: List[ValidationRule]) -> ValidationResult:
    """Run all rules against the report and return a combined result."""
    violations: List[str] = []

    for rule in rules:
        _check_rule(report, rule, violations)

    return ValidationResult(passed=len(violations) == 0, violations=violations)


def _check_rule(
    report: DiffReport,
    rule: ValidationRule,
    violations: List[str],
) -> None:
    """Apply a single rule and append any violations."""
    if rule.max_breaking_changes is not None:
        breaking = [c for c in report.changes if c.breaking]
        if len(breaking) > rule.max_breaking_changes:
            violations.append(
                f"[{rule.name}] Breaking changes ({len(breaking)}) exceed "
                f"allowed maximum ({rule.max_breaking_changes})."
            )

    if rule.severity_threshold is not None:
        order = [Severity.INFO, Severity.WARNING, Severity.ERROR]
        threshold_idx = order.index(rule.severity_threshold)
        for change in report.changes:
            if order.index(change.severity) >= threshold_idx:
                violations.append(
                    f"[{rule.name}] Change '{change.description}' has "
                    f"severity {change.severity.value} which meets or exceeds "
                    f"threshold {rule.severity_threshold.value}."
                )

    for forbidden in rule.forbidden_change_types:
        matches = [c for c in report.changes if c.change_type == forbidden]
        if matches:
            violations.append(
                f"[{rule.name}] Forbidden change type '{forbidden.value}' "
                f"found in {len(matches)} change(s)."
            )


def default_strict_rules() -> List[ValidationRule]:
    """Return a default set of strict validation rules."""
    return [
        ValidationRule(
            name="no-breaking-changes",
            description="Disallow any breaking changes.",
            max_breaking_changes=0,
        ),
        ValidationRule(
            name="no-removed-paths",
            description="Disallow removed paths.",
            forbidden_change_types=[ChangeType.REMOVED],
        ),
    ]
