"""Tests for apidiff.differ_extensions_defaults."""

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_defaults import diff_defaults


@pytest.fixture()
def base_spec() -> dict:
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Widget": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer", "default": 10},
                        "label": {"type": "string"},
                    },
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_defaults(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = dict(base_spec)
    new_spec["info"] = {"title": "Test API", "version": "2.0.0"}
    report = diff_defaults(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_default_is_breaking(base_spec):
    new_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Widget": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},  # default removed
                        "label": {"type": "string"},
                    },
                }
            }
        },
    }
    report = diff_defaults(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert change.change_type == ChangeType.REMOVED
    assert "count" in change.path


def test_added_default_is_non_breaking(base_spec):
    new_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Widget": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer", "default": 10},
                        "label": {"type": "string", "default": "n/a"},  # default added
                    },
                }
            }
        },
    }
    report = diff_defaults(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.NON_BREAKING
    assert change.change_type == ChangeType.ADDED
    assert "label" in change.path


def test_changed_default_is_non_breaking(base_spec):
    new_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Widget": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer", "default": 99},  # changed
                        "label": {"type": "string"},
                    },
                }
            }
        },
    }
    report = diff_defaults(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.NON_BREAKING
    assert change.change_type == ChangeType.MODIFIED
    assert "10" in change.description
    assert "99" in change.description


def test_no_schemas_returns_empty_report():
    old = {"openapi": "3.0.0", "info": {"title": "A", "version": "1.0"}, "paths": {}}
    new = {"openapi": "3.0.0", "info": {"title": "A", "version": "2.0"}, "paths": {}}
    report = diff_defaults(old, new)
    assert report.changes == []


def test_path_includes_schema_and_property(base_spec):
    new_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Widget": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "label": {"type": "string"},
                    },
                }
            }
        },
    }
    report = diff_defaults(base_spec, new_spec)
    assert any("Widget" in c.path and "count" in c.path for c in report.changes)
