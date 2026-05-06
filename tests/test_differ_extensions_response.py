"""Tests for differ_extensions_response module."""

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_response import diff_response_codes


@pytest.fixture
def base_spec():
    return {
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {"description": "OK"},
                        "404": {"description": "Not found"},
                    }
                },
                "post": {
                    "responses": {
                        "201": {"description": "Created"},
                    }
                },
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_response_codes(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = {**base_spec, "info": {"title": "Test API", "version": "2.0.0"}}
    report = diff_response_codes(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_response_code_is_breaking(base_spec):
    new_spec = {
        "info": {"title": "Test API", "version": "2.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {"description": "OK"},
                        # 404 removed
                    }
                },
                "post": {
                    "responses": {
                        "201": {"description": "Created"},
                    }
                },
            }
        },
    }
    report = diff_response_codes(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert len(breaking) == 1
    assert "404" in breaking[0].description
    assert breaking[0].change_type == ChangeType.REMOVED


def test_added_response_code_is_non_breaking(base_spec):
    new_spec = {
        "info": {"title": "Test API", "version": "2.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {"description": "OK"},
                        "404": {"description": "Not found"},
                        "429": {"description": "Rate limited"},
                    }
                },
                "post": {
                    "responses": {
                        "201": {"description": "Created"},
                    }
                },
            }
        },
    }
    report = diff_response_codes(base_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].severity == Severity.NON_BREAKING
    assert "429" in added[0].description


def test_change_path_and_operation_are_set(base_spec):
    new_spec = {
        "info": {"title": "Test API", "version": "2.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {"description": "OK"},
                    }
                },
                "post": {
                    "responses": {
                        "201": {"description": "Created"},
                    }
                },
            }
        },
    }
    report = diff_response_codes(base_spec, new_spec)
    removed = [c for c in report.changes if c.change_type == ChangeType.REMOVED]
    assert removed[0].path == "/users"
    assert removed[0].operation == "GET"


def test_empty_paths_returns_empty_report():
    old = {"info": {"title": "A", "version": "1.0"}, "paths": {}}
    new = {"info": {"title": "A", "version": "2.0"}, "paths": {}}
    report = diff_response_codes(old, new)
    assert report.changes == []
