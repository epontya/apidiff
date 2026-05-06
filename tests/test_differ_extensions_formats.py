"""Tests for apidiff/differ_extensions_formats.py"""

import pytest
from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_formats import diff_formats


@pytest.fixture
def base_spec():
    return {
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "birthdate": {"type": "string", "format": "date"},
                        "nickname": {"type": "string"},
                    }
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_formats(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = {"info": {"version": "2.0.0"}, "components": base_spec["components"]}
    report = diff_formats(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_format_is_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string"},  # format removed
                        "birthdate": {"type": "string", "format": "date"},
                        "nickname": {"type": "string"},
                    }
                }
            }
        },
    }
    report = diff_formats(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert change.change_type == ChangeType.REMOVED
    assert "email" in change.path
    assert "email" in change.description


def test_added_format_is_non_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "birthdate": {"type": "string", "format": "date"},
                        "nickname": {"type": "string", "format": "hostname"},  # added
                    }
                }
            }
        },
    }
    report = diff_formats(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.NON_BREAKING
    assert change.change_type == ChangeType.ADDED
    assert "nickname" in change.path


def test_modified_format_is_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "birthdate": {"type": "string", "format": "date-time"},  # changed
                        "nickname": {"type": "string"},
                    }
                }
            }
        },
    }
    report = diff_formats(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert change.change_type == ChangeType.MODIFIED
    assert "date" in change.description
    assert "date-time" in change.description


def test_missing_schema_in_new_spec_is_skipped(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": {"schemas": {}},
    }
    report = diff_formats(base_spec, new_spec)
    assert report.changes == []


def test_no_components_returns_empty_report():
    old = {"info": {"version": "1.0.0"}}
    new = {"info": {"version": "2.0.0"}}
    report = diff_formats(old, new)
    assert report.changes == []
