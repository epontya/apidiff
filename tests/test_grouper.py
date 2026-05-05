"""Tests for apidiff.grouper — change grouping by severity, path, and change_type."""

import pytest

from apidiff.differ import Change, ChangeType, DiffReport, Severity
from apidiff.grouper import (
    GroupedReport,
    group_by_severity,
    group_by_path_prefix,
    group_by_change_type,
    grouped_report_to_dict,
)


@pytest.fixture()
def mixed_report() -> DiffReport:
    return DiffReport(
        old_version="1.0",
        new_version="2.0",
        changes=[
            Change("/users", "GET", ChangeType.REMOVED, Severity.BREAKING, "Endpoint removed"),
            Change("/users", "POST", ChangeType.ADDED, Severity.NON_BREAKING, "Endpoint added"),
            Change("/items", "DELETE", ChangeType.REMOVED, Severity.BREAKING, "Item delete removed"),
            Change("/items", "GET", ChangeType.MODIFIED, Severity.NON_BREAKING, "Response changed"),
        ],
    )


@pytest.fixture()
def empty_report() -> DiffReport:
    return DiffReport(old_version="1.0", new_version="2.0", changes=[])


# --- group_by_severity ---

def test_group_by_severity_keys(mixed_report):
    grouped = group_by_severity(mixed_report)
    assert set(grouped.group_names()) == {Severity.BREAKING.value, Severity.NON_BREAKING.value}


def test_group_by_severity_breaking_count(mixed_report):
    grouped = group_by_severity(mixed_report)
    assert len(grouped.changes_for(Severity.BREAKING.value)) == 2


def test_group_by_severity_non_breaking_count(mixed_report):
    grouped = group_by_severity(mixed_report)
    assert len(grouped.changes_for(Severity.NON_BREAKING.value)) == 2


def test_group_by_severity_empty_report(empty_report):
    grouped = group_by_severity(empty_report)
    assert grouped.is_empty()


# --- group_by_path_prefix ---

def test_group_by_path_prefix_keys(mixed_report):
    grouped = group_by_path_prefix(mixed_report, depth=1)
    assert set(grouped.group_names()) == {"/users", "/items"}


def test_group_by_path_prefix_counts(mixed_report):
    grouped = group_by_path_prefix(mixed_report, depth=1)
    assert len(grouped.changes_for("/users")) == 2
    assert len(grouped.changes_for("/items")) == 2


def test_group_by_path_prefix_depth_zero(mixed_report):
    grouped = group_by_path_prefix(mixed_report, depth=0)
    # All paths collapse to root when depth=0
    assert "/" in grouped.group_names()
    assert len(grouped.changes_for("/")) == 4


# --- group_by_change_type ---

def test_group_by_change_type_keys(mixed_report):
    grouped = group_by_change_type(mixed_report)
    assert ChangeType.REMOVED.value in grouped.group_names()
    assert ChangeType.ADDED.value in grouped.group_names()


def test_group_by_change_type_removed_count(mixed_report):
    grouped = group_by_change_type(mixed_report)
    assert len(grouped.changes_for(ChangeType.REMOVED.value)) == 2


# --- grouped_report_to_dict ---

def test_grouped_report_to_dict_structure(mixed_report):
    grouped = group_by_severity(mixed_report)
    data = grouped_report_to_dict(grouped)
    assert data["old_version"] == "1.0"
    assert data["new_version"] == "2.0"
    assert isinstance(data["groups"], dict)


def test_grouped_report_to_dict_change_fields(mixed_report):
    grouped = group_by_severity(mixed_report)
    data = grouped_report_to_dict(grouped)
    first_change = next(iter(data["groups"].values()))[0]
    assert "path" in first_change
    assert "operation" in first_change
    assert "severity" in first_change
    assert "description" in first_change


def test_grouped_report_versions_preserved(mixed_report):
    grouped = group_by_change_type(mixed_report)
    assert grouped.old_version == "1.0"
    assert grouped.new_version == "2.0"
