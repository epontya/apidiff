"""Tests for apidiff.linter."""

import pytest

from apidiff.differ import Change, ChangeType, DiffReport, Severity
from apidiff.linter import LintIssue, LintResult, lint_report


@pytest.fixture
def empty_report():
    return DiffReport(old_version="1.0", new_version="2.0", changes=[])


@pytest.fixture
def breaking_no_description():
    return DiffReport(
        old_version="1.0",
        new_version="2.0",
        changes=[
            Change(
                path="/users",
                operation="GET",
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                description="",
            )
        ],
    )


@pytest.fixture
def duplicate_changes():
    change = Change(
        path="/items",
        operation="POST",
        change_type=ChangeType.MODIFIED,
        severity=Severity.NON_BREAKING,
        description="some change",
    )
    return DiffReport(old_version="1.0", new_version="2.0", changes=[change, change])


@pytest.fixture
def clean_report():
    return DiffReport(
        old_version="1.0",
        new_version="2.0",
        changes=[
            Change(
                path="/orders",
                operation="DELETE",
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                description="Endpoint removed in v2.",
            )
        ],
    )


def test_empty_report_has_no_issues(empty_report):
    result = lint_report(empty_report)
    assert result.issues == []


def test_clean_report_passes(clean_report):
    result = lint_report(clean_report)
    assert not result.has_errors()
    assert not result.has_warnings()


def test_breaking_without_description_raises_warning(breaking_no_description):
    result = lint_report(breaking_no_description)
    codes = [i.code for i in result.issues]
    assert "W001" in codes


def test_breaking_without_description_is_warning_not_error(breaking_no_description):
    result = lint_report(breaking_no_description)
    issue = next(i for i in result.issues if i.code == "W001")
    assert issue.severity == "warning"
    assert not result.has_errors()


def test_duplicate_change_raises_w002(duplicate_changes):
    result = lint_report(duplicate_changes)
    codes = [i.code for i in result.issues]
    assert "W002" in codes


def test_no_duplicate_in_clean_report(clean_report):
    result = lint_report(clean_report)
    codes = [i.code for i in result.issues]
    assert "W002" not in codes


def test_lint_result_bool_true_when_no_errors(empty_report):
    result = lint_report(empty_report)
    assert bool(result) is True


def test_lint_result_has_warnings_false_on_empty(empty_report):
    result = lint_report(empty_report)
    assert result.has_warnings() is False
