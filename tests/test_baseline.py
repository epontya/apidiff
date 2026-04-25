"""Tests for apidiff.baseline module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apidiff.baseline import (
    BaselineError,
    load_baseline,
    save_baseline,
    suppress_baseline,
)
from apidiff.differ import Change, ChangeType, DiffReport, Severity


@pytest.fixture()
def sample_change() -> Change:
    return Change(
        change_type=ChangeType.REMOVED,
        severity=Severity.BREAKING,
        path="/users",
        method="GET",
        description="Path removed",
    )


@pytest.fixture()
def sample_report(sample_change) -> DiffReport:
    return DiffReport(changes=[sample_change])


def test_save_baseline_creates_file(tmp_path, sample_report):
    dest = tmp_path / "baseline.json"
    save_baseline(sample_report, dest)
    assert dest.exists()


def test_save_baseline_content(tmp_path, sample_report, sample_change):
    dest = tmp_path / "baseline.json"
    save_baseline(sample_report, dest)
    data = json.loads(dest.read_text())
    assert len(data["changes"]) == 1
    assert data["changes"][0]["path"] == sample_change.path
    assert data["changes"][0]["change_type"] == sample_change.change_type.value


def test_load_baseline_returns_changes(tmp_path, sample_report, sample_change):
    dest = tmp_path / "baseline.json"
    save_baseline(sample_report, dest)
    changes = load_baseline(dest)
    assert len(changes) == 1
    assert changes[0].path == sample_change.path
    assert changes[0].severity == Severity.BREAKING


def test_load_baseline_missing_file_returns_empty(tmp_path):
    result = load_baseline(tmp_path / "nonexistent.json")
    assert result == []


def test_load_baseline_corrupt_file_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    with pytest.raises(BaselineError):
        load_baseline(bad)


def test_save_baseline_unwritable_path_raises(sample_report):
    with pytest.raises(BaselineError):
        save_baseline(sample_report, "/no_such_dir/baseline.json")


def test_suppress_baseline_removes_known_changes(sample_report, sample_change):
    result = suppress_baseline(sample_report, [sample_change])
    assert len(result.changes) == 0


def test_suppress_baseline_keeps_new_changes(sample_change):
    new_change = Change(
        change_type=ChangeType.ADDED,
        severity=Severity.NON_BREAKING,
        path="/items",
        method="POST",
        description="New endpoint",
    )
    report = DiffReport(changes=[sample_change, new_change])
    result = suppress_baseline(report, [sample_change])
    assert len(result.changes) == 1
    assert result.changes[0].path == "/items"


def test_suppress_baseline_empty_baseline_keeps_all(sample_report):
    result = suppress_baseline(sample_report, [])
    assert len(result.changes) == len(sample_report.changes)
