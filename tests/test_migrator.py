"""Unit tests for apidiff.migrator."""

import pytest

from apidiff.differ import Change, ChangeType, DiffReport, Severity
from apidiff.migrator import (
    MigrationHint,
    MigrationPlan,
    build_migration_plan,
    format_migration_plan,
)


@pytest.fixture()
def empty_report():
    return DiffReport(old_version="1.0", new_version="2.0", changes=[])


@pytest.fixture()
def breaking_report():
    return DiffReport(
        old_version="1.0",
        new_version="2.0",
        changes=[
            Change(
                path="/users",
                operation="get",
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                description="Path /users was removed",
            ),
            Change(
                path="/orders",
                operation="post",
                change_type=ChangeType.MODIFIED,
                severity=Severity.BREAKING,
                description="Request body field 'amount' type changed",
            ),
        ],
    )


@pytest.fixture()
def mixed_report():
    return DiffReport(
        old_version="1.0",
        new_version="2.0",
        changes=[
            Change(
                path="/users",
                operation="delete",
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                description="Endpoint removed",
            ),
            Change(
                path="/items",
                operation="get",
                change_type=ChangeType.ADDED,
                severity=Severity.NON_BREAKING,
                description="New endpoint added",
            ),
        ],
    )


def test_empty_report_produces_empty_plan(empty_report):
    plan = build_migration_plan(empty_report)
    assert plan.is_empty()


def test_plan_versions_match_report(breaking_report):
    plan = build_migration_plan(breaking_report)
    assert plan.old_version == "1.0"
    assert plan.new_version == "2.0"


def test_breaking_changes_produce_hints(breaking_report):
    plan = build_migration_plan(breaking_report)
    assert len(plan.hints) == 2


def test_non_breaking_changes_excluded(mixed_report):
    plan = build_migration_plan(mixed_report)
    assert len(plan.hints) == 1
    assert plan.hints[0].path == "/users"


def test_hint_fields_populated(breaking_report):
    plan = build_migration_plan(breaking_report)
    hint = plan.hints[0]
    assert hint.path == "/users"
    assert hint.operation == "get"
    assert hint.change_type == ChangeType.REMOVED.value
    assert hint.description
    assert hint.suggestion


def test_removed_suggestion_text(breaking_report):
    plan = build_migration_plan(breaking_report)
    removed_hint = next(h for h in plan.hints if h.change_type == "removed")
    assert "endpoint" in removed_hint.suggestion.lower() or "calls" in removed_hint.suggestion.lower()


def test_format_text_empty_plan(empty_report):
    plan = build_migration_plan(empty_report)
    text = format_migration_plan(plan)
    assert "No breaking changes" in text


def test_format_text_contains_path(breaking_report):
    plan = build_migration_plan(breaking_report)
    text = format_migration_plan(plan)
    assert "/users" in text
    assert "/orders" in text


def test_to_dict_structure(breaking_report):
    plan = build_migration_plan(breaking_report)
    d = plan.to_dict()
    assert "old_version" in d
    assert "new_version" in d
    assert isinstance(d["hints"], list)
    assert "suggestion" in d["hints"][0]
