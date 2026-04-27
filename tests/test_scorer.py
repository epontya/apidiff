"""Tests for apidiff.scorer."""

import pytest
from apidiff.differ import DiffReport, Change, ChangeType, Severity
from apidiff.scorer import (
    compute_score,
    format_score,
    score_to_dict,
    CompatibilityScore,
)


@pytest.fixture
def empty_report():
    return DiffReport(old_version="1.0", new_version="1.1", changes=[])


@pytest.fixture
def breaking_report():
    changes = [
        Change(
            change_type=ChangeType.REMOVED,
            severity=Severity.BREAKING,
            path="/users",
            operation="GET",
            description="Endpoint removed",
        )
    ]
    return DiffReport(old_version="1.0", new_version="1.1", changes=changes)


@pytest.fixture
def mixed_report():
    changes = [
        Change(
            change_type=ChangeType.REMOVED,
            severity=Severity.BREAKING,
            path="/users",
            operation="GET",
            description="Endpoint removed",
        ),
        Change(
            change_type=ChangeType.ADDED,
            severity=Severity.INFO,
            path="/items",
            operation="POST",
            description="New endpoint",
        ),
    ]
    return DiffReport(old_version="1.0", new_version="1.1", changes=changes)


def test_empty_report_scores_100(empty_report):
    cs = compute_score(empty_report)
    assert cs.score == 100


def test_empty_report_label_is_excellent(empty_report):
    cs = compute_score(empty_report)
    assert cs.label == "EXCELLENT"


def test_breaking_change_reduces_score(breaking_report):
    cs = compute_score(breaking_report)
    assert cs.score == 90  # 100 - 10


def test_score_never_goes_below_zero():
    changes = [
        Change(
            change_type=ChangeType.REMOVED,
            severity=Severity.BREAKING,
            path=f"/ep{i}",
            operation="DELETE",
            description="removed",
        )
        for i in range(20)  # penalty = 200 → clamped to 0
    ]
    report = DiffReport(old_version="1.0", new_version="2.0", changes=changes)
    cs = compute_score(report)
    assert cs.score == 0
    assert cs.label == "POOR"


def test_info_changes_do_not_reduce_score(mixed_report):
    cs = compute_score(mixed_report)
    # Only the BREAKING change should add penalty
    assert cs.penalty == 10
    assert cs.score == 90


def test_total_changes_counted(mixed_report):
    cs = compute_score(mixed_report)
    assert cs.total_changes == 2


def test_is_passing_above_threshold(empty_report):
    cs = compute_score(empty_report)
    assert cs.is_passing(threshold=80) is True


def test_is_failing_below_threshold(breaking_report):
    # score=90, threshold=95 → should fail
    cs = compute_score(breaking_report)
    assert cs.is_passing(threshold=95) is False


def test_format_score_contains_score(empty_report):
    cs = compute_score(empty_report)
    text = format_score(cs)
    assert "100/100" in text
    assert "EXCELLENT" in text


def test_score_to_dict_keys(empty_report):
    cs = compute_score(empty_report)
    d = score_to_dict(cs)
    assert set(d.keys()) == {"score", "label", "total_changes", "penalty"}


def test_score_to_dict_values(breaking_report):
    cs = compute_score(breaking_report)
    d = score_to_dict(cs)
    assert d["score"] == 90
    assert d["penalty"] == 10
