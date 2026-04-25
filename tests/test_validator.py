"""Tests for apidiff.validator module."""

import pytest

from apidiff.differ import Change, ChangeType, DiffReport, Severity
from apidiff.validator import (
    ValidationRule,
    ValidationResult,
    default_strict_rules,
    validate_report,
)


@pytest.fixture()
def empty_report() -> DiffReport:
    return DiffReport(changes=[])


@pytest.fixture()
def breaking_report() -> DiffReport:
    return DiffReport(
        changes=[
            Change(
                change_type=ChangeType.REMOVED,
                path="/users",
                method="GET",
                description="Path removed",
                breaking=True,
                severity=Severity.ERROR,
            )
        ]
    )


@pytest.fixture()
def info_report() -> DiffReport:
    return DiffReport(
        changes=[
            Change(
                change_type=ChangeType.ADDED,
                path="/items",
                method="POST",
                description="New path added",
                breaking=False,
                severity=Severity.INFO,
            )
        ]
    )


def test_empty_report_passes_strict_rules(empty_report):
    result = validate_report(empty_report, default_strict_rules())
    assert result.passed
    assert result.violations == []


def test_breaking_report_fails_no_breaking_rule(breaking_report):
    rules = [
        ValidationRule(
            name="no-breaking",
            description="No breaking changes allowed.",
            max_breaking_changes=0,
        )
    ]
    result = validate_report(breaking_report, rules)
    assert not result.passed
    assert any("no-breaking" in v for v in result.violations)


def test_forbidden_change_type_triggers_violation(breaking_report):
    rules = [
        ValidationRule(
            name="no-removals",
            description="No removals.",
            forbidden_change_types=[ChangeType.REMOVED],
        )
    ]
    result = validate_report(breaking_report, rules)
    assert not result.passed
    assert any("REMOVED" in v or "removed" in v.lower() for v in result.violations)


def test_severity_threshold_error_triggers_on_error_change(breaking_report):
    rules = [
        ValidationRule(
            name="no-errors",
            description="No error-level changes.",
            severity_threshold=Severity.ERROR,
        )
    ]
    result = validate_report(breaking_report, rules)
    assert not result.passed


def test_severity_threshold_does_not_trigger_on_info(info_report):
    rules = [
        ValidationRule(
            name="no-errors",
            description="No error-level changes.",
            severity_threshold=Severity.ERROR,
        )
    ]
    result = validate_report(info_report, rules)
    assert result.passed


def test_validation_result_bool_false_when_violations():
    result = ValidationResult(passed=False, violations=["something"])
    assert not bool(result)


def test_validation_result_bool_true_when_no_violations():
    result = ValidationResult(passed=True, violations=[])
    assert bool(result)


def test_default_strict_rules_returns_list():
    rules = default_strict_rules()
    assert len(rules) >= 2
    names = [r.name for r in rules]
    assert "no-breaking-changes" in names
    assert "no-removed-paths" in names
