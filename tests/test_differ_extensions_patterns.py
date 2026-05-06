"""Tests for apidiff.differ_extensions_patterns."""

from __future__ import annotations

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_patterns import diff_patterns


@pytest.fixture()
def base_spec() -> dict:
    return {
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string", "pattern": "^[\\w.]+@[\\w]+\\.[a-z]{2,}$"},
                        "name": {"type": "string"},
                    }
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_patterns(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = dict(base_spec)
    new_spec["info"] = {"version": "2.0.0"}
    report = diff_patterns(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_pattern_is_non_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string"},
                        "name": {"type": "string"},
                    }
                }
            }
        },
    }
    report = diff_patterns(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.NON_BREAKING
    assert change.change_type == ChangeType.REMOVED
    assert "email" in change.description


def test_added_pattern_is_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string", "pattern": "^[\\w.]+@[\\w]+\\.[a-z]{2,}$"},
                        "name": {"type": "string", "pattern": "^[A-Za-z]+$"},
                    }
                }
            }
        },
    }
    report = diff_patterns(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert change.change_type == ChangeType.ADDED
    assert "name" in change.description


def test_changed_pattern_is_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string", "pattern": "^.+@.+$"},
                        "name": {"type": "string"},
                    }
                }
            }
        },
    }
    report = diff_patterns(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert change.change_type == ChangeType.MODIFIED


def test_path_contains_schema_and_property(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string"},
                        "name": {"type": "string"},
                    }
                }
            }
        },
    }
    report = diff_patterns(base_spec, new_spec)
    assert "User" in report.changes[0].path
    assert "email" in report.changes[0].path


def test_no_schemas_returns_empty_report():
    old = {"info": {"version": "1.0.0"}}
    new = {"info": {"version": "2.0.0"}}
    report = diff_patterns(old, new)
    assert report.changes == []
