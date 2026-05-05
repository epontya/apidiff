"""Tests for apidiff.tagger and apidiff.tagger_cmd."""

import json
import pytest

from apidiff.differ import Change, ChangeType, Severity, DiffReport
from apidiff.tagger import tag_report, TaggedReport, _extract_tags


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def old_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"tags": ["users"], "summary": "List users"},
                "post": {"tags": ["users"], "summary": "Create user"},
            },
            "/orders": {
                "get": {"tags": ["orders"], "summary": "List orders"},
            },
        },
    }


@pytest.fixture()
def new_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "2.0.0"},
        "paths": {
            "/users": {
                "get": {"tags": ["users"], "summary": "List users"},
            },
        },
    }


def _make_report(*changes) -> DiffReport:
    return DiffReport(old_version="1.0.0", new_version="2.0.0", changes=list(changes))


def _make_change(path, operation, change_type=ChangeType.REMOVED, severity=Severity.BREAKING):
    return Change(
        path=path,
        operation=operation,
        change_type=change_type,
        severity=severity,
        description=f"{change_type.value} {operation} {path}",
    )


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_extract_tags_found(old_spec):
    tags = _extract_tags(old_spec, "/users", "get")
    assert tags == ["users"]


def test_extract_tags_missing_operation(old_spec):
    tags = _extract_tags(old_spec, "/users", "delete")
    assert tags == []


def test_extract_tags_none_operation(old_spec):
    assert _extract_tags(old_spec, "/users", None) == []


def test_tag_report_preserves_versions(old_spec, new_spec):
    report = _make_report()
    tagged = tag_report(report, old_spec, new_spec)
    assert tagged.old_version == "1.0.0"
    assert tagged.new_version == "2.0.0"


def test_tag_report_empty_is_empty(old_spec, new_spec):
    report = _make_report()
    tagged = tag_report(report, old_spec, new_spec)
    assert tagged.is_empty()


def test_tag_report_assigns_tags_from_new_spec(old_spec, new_spec):
    change = _make_change("/users", "get")
    report = _make_report(change)
    tagged = tag_report(report, old_spec, new_spec)
    assert tagged.tagged_changes[0].tags == ["users"]


def test_tag_report_falls_back_to_old_spec(old_spec, new_spec):
    # /orders only exists in old_spec
    change = _make_change("/orders", "get")
    report = _make_report(change)
    tagged = tag_report(report, old_spec, new_spec)
    assert tagged.tagged_changes[0].tags == ["orders"]


def test_tag_report_untagged_operation(old_spec, new_spec):
    change = _make_change("/unknown", "get")
    report = _make_report(change)
    tagged = tag_report(report, old_spec, new_spec)
    assert tagged.tagged_changes[0].tags == []


def test_all_tags_returns_sorted(old_spec, new_spec):
    changes = [
        _make_change("/orders", "get"),
        _make_change("/users", "get"),
    ]
    tagged = tag_report(_make_report(*changes), old_spec, new_spec)
    assert tagged.all_tags() == ["orders", "users"]


def test_changes_for_tag_filters_correctly(old_spec, new_spec):
    changes = [
        _make_change("/orders", "get"),
        _make_change("/users", "get"),
    ]
    tagged = tag_report(_make_report(*changes), old_spec, new_spec)
    user_changes = tagged.changes_for_tag("users")
    assert len(user_changes) == 1
    assert user_changes[0].change.path == "/users"


def test_to_dict_contains_expected_keys(old_spec, new_spec):
    change = _make_change("/users", "get")
    tagged = tag_report(_make_report(change), old_spec, new_spec)
    d = tagged.tagged_changes[0].to_dict()
    assert "tags" in d
    assert "path" in d
    assert "severity" in d
    assert "change_type" in d
