"""Tests for apidiff.differ_tags."""

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_tags import diff_tags


@pytest.fixture()
def base_spec() -> dict:
    return {
        "info": {"version": "1.0.0"},
        "tags": [{"name": "users"}, {"name": "admin"}],
        "paths": {
            "/users": {
                "get": {"tags": ["users"], "responses": {"200": {"description": "ok"}}},
                "post": {"tags": ["users", "admin"], "responses": {"201": {"description": "created"}}},
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_tags(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = {**base_spec, "info": {"version": "2.0.0"}}
    report = diff_tags(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_global_tag_is_non_breaking(base_spec):
    new_spec = {**base_spec, "tags": [{"name": "users"}]}
    report = diff_tags(base_spec, new_spec)
    removed = [c for c in report.changes if c.change_type == ChangeType.REMOVED and "admin" in c.description]
    assert len(removed) == 1
    assert removed[0].severity == Severity.NON_BREAKING


def test_added_global_tag_is_non_breaking(base_spec):
    new_spec = {**base_spec, "tags": [{"name": "users"}, {"name": "admin"}, {"name": "billing"}]}
    report = diff_tags(base_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED and "billing" in c.description]
    assert len(added) == 1
    assert added[0].severity == Severity.NON_BREAKING


def test_removed_operation_tag_is_non_breaking(base_spec):
    new_spec = {
        **base_spec,
        "paths": {
            "/users": {
                "get": {"tags": ["users"], "responses": {"200": {"description": "ok"}}},
                "post": {"tags": ["users"], "responses": {"201": {"description": "created"}}},
            }
        },
    }
    report = diff_tags(base_spec, new_spec)
    removed = [c for c in report.changes if c.change_type == ChangeType.REMOVED and "admin" in c.description]
    assert len(removed) == 1
    assert removed[0].path == "/users"
    assert removed[0].operation == "POST"
    assert removed[0].severity == Severity.NON_BREAKING


def test_added_operation_tag_is_non_breaking(base_spec):
    new_spec = {
        **base_spec,
        "paths": {
            "/users": {
                "get": {"tags": ["users", "public"], "responses": {"200": {"description": "ok"}}},
                "post": {"tags": ["users", "admin"], "responses": {"201": {"description": "created"}}},
            }
        },
    }
    report = diff_tags(base_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED and "public" in c.description]
    assert len(added) == 1
    assert added[0].severity == Severity.NON_BREAKING


def test_no_changes_when_tags_absent():
    spec = {"info": {"version": "1.0.0"}, "paths": {}}
    report = diff_tags(spec, spec)
    assert report.changes == []


def test_all_changes_are_non_breaking(base_spec):
    new_spec = {
        **base_spec,
        "tags": [{"name": "users"}, {"name": "newTag"}],
        "paths": {
            "/users": {
                "get": {"tags": [], "responses": {"200": {"description": "ok"}}},
                "post": {"tags": ["users", "admin"], "responses": {"201": {"description": "created"}}},
            }
        },
    }
    report = diff_tags(base_spec, new_spec)
    assert all(c.severity == Severity.NON_BREAKING for c in report.changes)
