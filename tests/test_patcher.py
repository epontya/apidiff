"""Tests for apidiff.patcher — patch suggestion generation."""

import pytest

from apidiff.differ import Change, ChangeType, Severity, DiffReport
from apidiff.patcher import (
    PatchSuggestion,
    PatchPlan,
    build_patch_plan,
    format_patch_plan,
)


@pytest.fixture
def empty_report():
    return DiffReport(old_version="1.0", new_version="2.0", changes=[])


@pytest.fixture
def breaking_report():
    return DiffReport(
        old_version="1.0",
        new_version="2.0",
        changes=[
            Change(
                path="/users",
                operation="GET",
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                description="Path removed",
                breaking=True,
            )
        ],
    )


@pytest.fixture
def mixed_report():
    return DiffReport(
        old_version="1.0",
        new_version="2.0",
        changes=[
            Change(
                path="/users",
                operation="GET",
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                description="Path removed",
                breaking=True,
            ),
            Change(
                path="/items",
                operation="POST",
                change_type=ChangeType.ADDED,
                severity=Severity.NON_BREAKING,
                description="New endpoint added",
                breaking=False,
            ),
        ],
    )


def test_empty_report_produces_empty_plan(empty_report):
    plan = build_patch_plan(empty_report)
    assert plan.is_empty()


def test_empty_plan_versions_match_report(empty_report):
    plan = build_patch_plan(empty_report)
    assert plan.old_version == "1.0"
    assert plan.new_version == "2.0"


def test_breaking_report_produces_one_suggestion(breaking_report):
    plan = build_patch_plan(breaking_report)
    assert len(plan.suggestions) == 1


def test_suggestion_path_matches_change(breaking_report):
    plan = build_patch_plan(breaking_report)
    assert plan.suggestions[0].path == "/users"


def test_suggestion_operation_matches_change(breaking_report):
    plan = build_patch_plan(breaking_report)
    assert plan.suggestions[0].operation == "GET"


def test_non_breaking_changes_excluded(mixed_report):
    plan = build_patch_plan(mixed_report)
    paths = [s.path for s in plan.suggestions]
    assert "/items" not in paths


def test_suggestion_to_dict_has_required_keys(breaking_report):
    plan = build_patch_plan(breaking_report)
    d = plan.suggestions[0].to_dict()
    assert "path" in d
    assert "operation" in d
    assert "change_type" in d
    assert "description" in d
    assert "suggestion" in d


def test_plan_to_dict_structure(breaking_report):
    plan = build_patch_plan(breaking_report)
    d = plan.to_dict()
    assert d["old_version"] == "1.0"
    assert d["new_version"] == "2.0"
    assert isinstance(d["suggestions"], list)


def test_format_empty_plan_message(empty_report):
    plan = build_patch_plan(empty_report)
    text = format_patch_plan(plan)
    assert "No breaking changes" in text


def test_format_breaking_plan_contains_path(breaking_report):
    plan = build_patch_plan(breaking_report)
    text = format_patch_plan(plan)
    assert "/users" in text


def test_format_breaking_plan_contains_suggestion(breaking_report):
    plan = build_patch_plan(breaking_report)
    text = format_patch_plan(plan)
    assert "Suggestion" in text
