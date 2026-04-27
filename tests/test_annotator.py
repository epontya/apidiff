"""Tests for apidiff.annotator."""

import pytest

from apidiff.differ import Change, ChangeType, DiffReport, Severity
from apidiff.annotator import AnnotatedChange, annotate_report


@pytest.fixture()
def empty_report():
    return DiffReport(version_old="1.0.0", version_new="2.0.0", changes=[])


@pytest.fixture()
def breaking_report():
    return DiffReport(
        version_old="1.0.0",
        version_new="2.0.0",
        changes=[
            Change(
                change_type=ChangeType.REMOVED_PATH,
                severity=Severity.BREAKING,
                path="/users",
                operation=None,
                details={},
            ),
            Change(
                change_type=ChangeType.ADDED_REQUIRED_PARAMETER,
                severity=Severity.BREAKING,
                path="/orders",
                operation="post",
                details={"name": "customer_id"},
            ),
        ],
    )


def test_annotate_empty_report_is_empty(empty_report):
    result = annotate_report(empty_report)
    assert result.is_empty()


def test_annotate_preserves_versions(breaking_report):
    result = annotate_report(breaking_report)
    assert result.version_old == "1.0.0"
    assert result.version_new == "2.0.0"


def test_annotate_produces_one_entry_per_change(breaking_report):
    result = annotate_report(breaking_report)
    assert len(result.annotated) == len(breaking_report.changes)


def test_removed_path_hint_contains_path(breaking_report):
    result = annotate_report(breaking_report)
    entry = result.annotated[0]
    assert "/users" in entry.hint


def test_removed_path_effort_is_high(breaking_report):
    result = annotate_report(breaking_report)
    assert result.annotated[0].migration_effort == "high"


def test_added_required_param_hint_contains_name(breaking_report):
    result = annotate_report(breaking_report)
    entry = result.annotated[1]
    assert "customer_id" in entry.hint


def test_added_required_param_effort_is_high(breaking_report):
    result = annotate_report(breaking_report)
    assert result.annotated[1].migration_effort == "high"


def test_non_breaking_change_has_low_effort():
    report = DiffReport(
        version_old="1.0",
        version_new="1.1",
        changes=[
            Change(
                change_type=ChangeType.ADDED_PATH,
                severity=Severity.NON_BREAKING,
                path="/health",
                operation=None,
                details={},
            )
        ],
    )
    result = annotate_report(report)
    assert result.annotated[0].migration_effort == "low"
