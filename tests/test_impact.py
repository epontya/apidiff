"""Tests for apidiff.impact — ImpactReport construction and formatting."""

import pytest

from apidiff.differ import Change, ChangeType, Severity, DiffReport
from apidiff.impact import (
    ImpactedArea,
    ImpactReport,
    build_impact_report,
    format_impact_report,
    impact_to_dict,
)


@pytest.fixture()
def empty_report():
    return DiffReport(old_version="1.0", new_version="2.0", changes=[])


@pytest.fixture()
def breaking_report():
    changes = [
        Change(
            change_type=ChangeType.REMOVED,
            severity=Severity.BREAKING,
            path="/users",
            operation="GET",
            description="Endpoint removed",
        ),
        Change(
            change_type=ChangeType.MODIFIED,
            severity=Severity.BREAKING,
            path="/users",
            operation="POST",
            description="Request body changed",
        ),
        Change(
            change_type=ChangeType.REMOVED,
            severity=Severity.BREAKING,
            path="/items",
            operation="DELETE",
            description="Endpoint removed",
        ),
    ]
    return DiffReport(old_version="1.0", new_version="2.0", changes=changes)


@pytest.fixture()
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
            severity=Severity.NON_BREAKING,
            path="/users",
            operation="PATCH",
            description="New endpoint added",
        ),
    ]
    return DiffReport(old_version="1.0", new_version="2.0", changes=changes)


def test_empty_report_produces_empty_impact(empty_report):
    impact = build_impact_report(empty_report)
    assert impact.is_empty()


def test_breaking_report_has_impacted_areas(breaking_report):
    impact = build_impact_report(breaking_report)
    assert not impact.is_empty()


def test_total_impacted_paths(breaking_report):
    impact = build_impact_report(breaking_report)
    assert impact.total_impacted_paths() == 2


def test_has_breaking_true(breaking_report):
    impact = build_impact_report(breaking_report)
    assert impact.has_breaking()


def test_mixed_report_only_breaking_counted(mixed_report):
    impact = build_impact_report(mixed_report)
    # only the breaking change on /users should be in the impact report
    assert impact.total_impacted_paths() == 1


def test_format_impact_report_contains_path(breaking_report):
    impact = build_impact_report(breaking_report)
    text = format_impact_report(impact)
    assert "/users" in text
    assert "/items" in text


def test_format_empty_impact_report(empty_report):
    impact = build_impact_report(empty_report)
    text = format_impact_report(impact)
    assert "No impacted" in text or text.strip() != ""


def test_impact_to_dict_structure(breaking_report):
    impact = build_impact_report(breaking_report)
    d = impact_to_dict(impact)
    assert "impacted_areas" in d
    assert "total_impacted_paths" in d
    assert isinstance(d["impacted_areas"], list)


def test_impact_to_dict_operations(breaking_report):
    impact = build_impact_report(breaking_report)
    d = impact_to_dict(impact)
    paths = {area["path"] for area in d["impacted_areas"]}
    assert "/users" in paths
    assert "/items" in paths
