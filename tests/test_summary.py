"""Tests for apidiff/summary.py"""

import pytest
from apidiff.differ import ChangeType, Severity, Change, DiffReport
from apidiff.summary import summarize, format_summary, DiffSummary


@pytest.fixture
def mixed_report():
    return DiffReport(changes=[
        Change(path="/a", change_type=ChangeType.REMOVED, severity=Severity.BREAKING,
               description="Removed /a"),
        Change(path="/b", change_type=ChangeType.REMOVED, severity=Severity.BREAKING,
               description="Removed /b"),
        Change(path="/c", change_type=ChangeType.ADDED, severity=Severity.NON_BREAKING,
               description="Added /c"),
        Change(path="/d", change_type=ChangeType.MODIFIED, severity=Severity.NON_BREAKING,
               description="Modified /d"),
    ])


def test_summarize_total(mixed_report):
    summary = summarize(mixed_report)
    assert summary.total == 4


def test_summarize_breaking_count(mixed_report):
    summary = summarize(mixed_report)
    assert summary.breaking == 2


def test_summarize_non_breaking_count(mixed_report):
    summary = summarize(mixed_report)
    assert summary.non_breaking == 2


def test_summarize_by_type(mixed_report):
    summary = summarize(mixed_report)
    assert summary.by_type.get(ChangeType.REMOVED.value, 0) == 2
    assert summary.by_type.get(ChangeType.ADDED.value, 0) == 1
    assert summary.by_type.get(ChangeType.MODIFIED.value, 0) == 1


def test_summarize_empty_report():
    summary = summarize(DiffReport(changes=[]))
    assert summary.total == 0
    assert summary.breaking == 0
    assert summary.non_breaking == 0
    assert summary.by_type == {}


def test_summary_as_dict(mixed_report):
    summary = summarize(mixed_report)
    d = summary.as_dict()
    assert d["total"] == 4
    assert d["breaking"] == 2
    assert d["non_breaking"] == 2
    assert isinstance(d["by_type"], dict)


def test_format_summary_contains_totals(mixed_report):
    summary = summarize(mixed_report)
    text = format_summary(summary)
    assert "Total changes" in text
    assert "Breaking" in text
    assert "Non-breaking" in text


def test_format_summary_lists_types(mixed_report):
    summary = summarize(mixed_report)
    text = format_summary(summary)
    assert ChangeType.REMOVED.value in text
    assert ChangeType.ADDED.value in text
