"""Unit tests for apidiff.tracer."""

from __future__ import annotations

import pytest

from apidiff.differ import Change, ChangeType, DiffReport, Severity
from apidiff.tracer import TraceResult, format_trace, trace_changes


@pytest.fixture()
def mixed_report() -> DiffReport:
    return DiffReport(
        old_version="1.0.0",
        new_version="2.0.0",
        changes=[
            Change("/users", ChangeType.REMOVED, Severity.BREAKING, "Path removed"),
            Change("/users.get", ChangeType.MODIFIED, Severity.NON_BREAKING, "Description changed"),
            Change("/orders.post", ChangeType.MODIFIED, Severity.BREAKING, "Request body changed"),
            Change("/health.get", ChangeType.MODIFIED, Severity.NON_BREAKING, "Added field"),
        ],
    )


def test_trace_matches_exact_path(mixed_report: DiffReport) -> None:
    result = trace_changes(mixed_report, "/users")
    paths = [c.path for c in result.matched]
    assert "/users" in paths
    assert "/users.get" in paths


def test_trace_glob_matches_multiple(mixed_report: DiffReport) -> None:
    result = trace_changes(mixed_report, "/users*")
    assert len(result.matched) == 2


def test_trace_no_match_returns_empty(mixed_report: DiffReport) -> None:
    result = trace_changes(mixed_report, "/nonexistent")
    assert result.is_empty()


def test_trace_operation_filter(mixed_report: DiffReport) -> None:
    result = trace_changes(mixed_report, "/users*", operation="get")
    assert len(result.matched) == 1
    assert result.matched[0].path == "/users.get"


def test_trace_has_breaking_true(mixed_report: DiffReport) -> None:
    result = trace_changes(mixed_report, "/orders*")
    assert result.has_breaking() is True


def test_trace_has_breaking_false(mixed_report: DiffReport) -> None:
    result = trace_changes(mixed_report, "/health*")
    assert result.has_breaking() is False


def test_trace_breaking_changes_list(mixed_report: DiffReport) -> None:
    result = trace_changes(mixed_report, "/orders*")
    breaking = result.breaking_changes()
    assert len(breaking) == 1
    assert breaking[0].severity == Severity.BREAKING


def test_trace_non_breaking_changes_list(mixed_report: DiffReport) -> None:
    result = trace_changes(mixed_report, "/users*")
    non_breaking = result.non_breaking_changes()
    assert all(c.severity == Severity.NON_BREAKING for c in non_breaking)


def test_trace_result_versions(mixed_report: DiffReport) -> None:
    result = trace_changes(mixed_report, "/users")
    assert result.old_version == "1.0.0"
    assert result.new_version == "2.0.0"


def test_format_trace_empty() -> None:
    result = TraceResult(old_version="1.0", new_version="2.0", pattern="/x")
    text = format_trace(result)
    assert "no changes matched" in text
    assert "/x" in text


def test_format_trace_non_empty(mixed_report: DiffReport) -> None:
    result = trace_changes(mixed_report, "/orders*")
    text = format_trace(result)
    assert "[BREAKING]" in text
    assert "/orders.post" in text
