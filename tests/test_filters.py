"""Tests for apidiff/filters.py"""

import pytest
from apidiff.differ import ChangeType, Severity, Change, DiffReport
from apidiff.filters import (
    filter_by_severity,
    filter_by_change_type,
    filter_by_path_prefix,
    filter_breaking_only,
    filter_non_breaking_only,
    combine_reports,
)


@pytest.fixture
def sample_report():
    return DiffReport(changes=[
        Change(path="/users", change_type=ChangeType.REMOVED, severity=Severity.BREAKING,
               description="Path /users removed"),
        Change(path="/users/{id}", change_type=ChangeType.ADDED, severity=Severity.NON_BREAKING,
               description="Path /users/{id} added"),
        Change(path="/orders", change_type=ChangeType.MODIFIED, severity=Severity.BREAKING,
               description="Required field removed from /orders"),
        Change(path="/health", change_type=ChangeType.ADDED, severity=Severity.NON_BREAKING,
               description="Path /health added"),
    ])


def test_filter_breaking_only(sample_report):
    result = filter_breaking_only(sample_report)
    assert len(result.changes) == 2
    assert all(c.severity == Severity.BREAKING for c in result.changes)


def test_filter_non_breaking_only(sample_report):
    result = filter_non_breaking_only(sample_report)
    assert len(result.changes) == 2
    assert all(c.severity != Severity.BREAKING for c in result.changes)


def test_filter_by_severity_breaking(sample_report):
    result = filter_by_severity(sample_report, Severity.BREAKING)
    assert len(result.changes) == 2


def test_filter_by_severity_non_breaking(sample_report):
    result = filter_by_severity(sample_report, Severity.NON_BREAKING)
    assert len(result.changes) == 4


def test_filter_by_change_type_removed(sample_report):
    result = filter_by_change_type(sample_report, ChangeType.REMOVED)
    assert len(result.changes) == 1
    assert result.changes[0].path == "/users"


def test_filter_by_change_type_added(sample_report):
    result = filter_by_change_type(sample_report, ChangeType.ADDED)
    assert len(result.changes) == 2


def test_filter_by_path_prefix_users(sample_report):
    result = filter_by_path_prefix(sample_report, "/users")
    assert len(result.changes) == 2
    assert all(c.path.startswith("/users") for c in result.changes)


def test_filter_by_path_prefix_no_match(sample_report):
    result = filter_by_path_prefix(sample_report, "/nonexistent")
    assert len(result.changes) == 0


def test_combine_reports():
    r1 = DiffReport(changes=[
        Change(path="/a", change_type=ChangeType.ADDED, severity=Severity.NON_BREAKING,
               description="Added /a")
    ])
    r2 = DiffReport(changes=[
        Change(path="/b", change_type=ChangeType.REMOVED, severity=Severity.BREAKING,
               description="Removed /b")
    ])
    combined = combine_reports(r1, r2)
    assert len(combined.changes) == 2


def test_combine_empty_reports():
    result = combine_reports(DiffReport(changes=[]), DiffReport(changes=[]))
    assert result.changes == []
