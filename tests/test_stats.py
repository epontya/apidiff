"""Tests for apidiff.stats module."""

import pytest

from apidiff.differ import DiffReport, Change, ChangeType, Severity
from apidiff.stats import compute_stats, stats_to_dict, format_stats, DiffStats


@pytest.fixture
def empty_report():
    return DiffReport(old_version="1.0", new_version="2.0", changes=[])


@pytest.fixture
def mixed_report():
    return DiffReport(
        old_version="1.0",
        new_version="2.0",
        changes=[
            Change(
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                path="/users",
                operation="GET",
                description="Path removed",
                breaking=True,
            ),
            Change(
                change_type=ChangeType.ADDED,
                severity=Severity.NON_BREAKING,
                path="/items",
                operation="POST",
                description="Path added",
                breaking=False,
            ),
            Change(
                change_type=ChangeType.MODIFIED,
                severity=Severity.BREAKING,
                path="/users",
                operation="POST",
                description="Parameter removed",
                breaking=True,
            ),
        ],
    )


def test_empty_report_stats_are_zero(empty_report):
    stats = compute_stats(empty_report)
    assert stats.total == 0
    assert stats.breaking == 0
    assert stats.non_breaking == 0
    assert stats.breaking_ratio == 0.0
    assert stats.affected_paths == []


def test_total_count(mixed_report):
    stats = compute_stats(mixed_report)
    assert stats.total == 3


def test_breaking_count(mixed_report):
    stats = compute_stats(mixed_report)
    assert stats.breaking == 2


def test_non_breaking_count(mixed_report):
    stats = compute_stats(mixed_report)
    assert stats.non_breaking == 1


def test_breaking_ratio(mixed_report):
    stats = compute_stats(mixed_report)
    assert stats.breaking_ratio == pytest.approx(2 / 3, rel=1e-3)


def test_by_severity_keys(mixed_report):
    stats = compute_stats(mixed_report)
    assert stats.by_severity.get(Severity.BREAKING.value, 0) == 2
    assert stats.by_severity.get(Severity.NON_BREAKING.value, 0) == 1


def test_by_change_type_keys(mixed_report):
    stats = compute_stats(mixed_report)
    assert stats.by_change_type.get(ChangeType.REMOVED.value, 0) == 1
    assert stats.by_change_type.get(ChangeType.ADDED.value, 0) == 1
    assert stats.by_change_type.get(ChangeType.MODIFIED.value, 0) == 1


def test_affected_paths_deduplicated(mixed_report):
    stats = compute_stats(mixed_report)
    # /users appears twice but should be listed once
    assert len(stats.affected_paths) == 2
    assert "/users" in stats.affected_paths
    assert "/items" in stats.affected_paths


def test_stats_to_dict_keys(mixed_report):
    stats = compute_stats(mixed_report)
    d = stats_to_dict(stats)
    assert "total" in d
    assert "breaking" in d
    assert "non_breaking" in d
    assert "breaking_ratio" in d
    assert "by_severity" in d
    assert "by_change_type" in d
    assert "affected_paths" in d


def test_format_stats_returns_string(mixed_report):
    stats = compute_stats(mixed_report)
    text = format_stats(stats)
    assert isinstance(text, str)
    assert "Breaking" in text
    assert "Total" in text
