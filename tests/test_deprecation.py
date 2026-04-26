"""Tests for apidiff.deprecation module."""

import pytest
from apidiff.deprecation import (
    detect_deprecations,
    deprecation_report_to_changes,
    DeprecationReport,
)
from apidiff.differ import ChangeType, Severity


@pytest.fixture
def old_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {
            "/users": {
                "get": {"summary": "List users", "deprecated": False},
                "post": {"summary": "Create user"},
            },
            "/items": {
                "get": {"summary": "List items", "deprecated": True},
            },
        },
    }


@pytest.fixture
def new_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "2.0"},
        "paths": {
            "/users": {
                "get": {"summary": "List users", "deprecated": True},
                "post": {"summary": "Create user"},
            },
            "/items": {
                "get": {"summary": "List items", "deprecated": False},
            },
        },
    }


def test_detect_newly_deprecated(old_spec, new_spec):
    report = detect_deprecations(old_spec, new_spec)
    assert len(report.newly_deprecated) == 1
    warn = report.newly_deprecated[0]
    assert warn.path == "/users"
    assert warn.method == "GET"


def test_detect_removed_deprecated(old_spec, new_spec):
    report = detect_deprecations(old_spec, new_spec)
    assert len(report.removed_deprecated) == 1
    warn = report.removed_deprecated[0]
    assert warn.path == "/items"
    assert warn.method == "GET"


def test_no_deprecation_changes_returns_empty_report(old_spec):
    report = detect_deprecations(old_spec, old_spec)
    assert report.is_empty()


def test_newly_deprecated_path_not_in_old(old_spec):
    new = {
        "openapi": "3.0.0",
        "info": {"title": "T", "version": "2.0"},
        "paths": {
            "/new-endpoint": {
                "get": {"summary": "New", "deprecated": True},
            }
        },
    }
    report = detect_deprecations(old_spec, new)
    assert len(report.newly_deprecated) == 1
    assert report.newly_deprecated[0].path == "/new-endpoint"


def test_deprecation_report_to_dict(old_spec, new_spec):
    report = detect_deprecations(old_spec, new_spec)
    d = report.to_dict()
    assert "newly_deprecated" in d
    assert "removed_deprecated" in d
    assert d["newly_deprecated"][0]["method"] == "GET"


def test_deprecation_report_to_changes(old_spec, new_spec):
    dep_report = detect_deprecations(old_spec, new_spec)
    changes = deprecation_report_to_changes(dep_report)
    assert len(changes) == 2
    types = {c.change_type for c in changes}
    assert ChangeType.DEPRECATED in types


def test_all_changes_are_non_breaking(old_spec, new_spec):
    dep_report = detect_deprecations(old_spec, new_spec)
    changes = deprecation_report_to_changes(dep_report)
    for change in changes:
        assert change.severity == Severity.NON_BREAKING


def test_deprecation_warning_description_contains_path(old_spec, new_spec):
    report = detect_deprecations(old_spec, new_spec)
    warn = report.newly_deprecated[0]
    assert "/users" in warn.description
