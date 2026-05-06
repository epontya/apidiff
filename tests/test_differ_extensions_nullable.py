"""Tests for apidiff.differ_extensions_nullable."""
from __future__ import annotations

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_nullable import diff_nullable


@pytest.fixture()
def base_spec() -> dict:
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "nickname": {"type": "string", "nullable": True},
                    },
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_nullable(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = {**base_spec, "info": {"title": "Test API", "version": "2.0.0"}}
    report = diff_nullable(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_nullable_removed_is_breaking(base_spec):
    """Removing nullable:true from a property is a breaking change."""
    new_spec = {
        **base_spec,
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "nickname": {"type": "string"},  # nullable removed
                    },
                }
            }
        },
    }
    report = diff_nullable(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert change.change_type == ChangeType.MODIFIED
    assert "nickname" in change.path
    assert "User" in change.path


def test_nullable_added_is_non_breaking(base_spec):
    """Adding nullable:true to a property is non-breaking."""
    new_spec = {
        **base_spec,
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "nullable": True},  # added
                        "nickname": {"type": "string", "nullable": True},
                    },
                }
            }
        },
    }
    report = diff_nullable(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.NON_BREAKING
    assert "name" in change.path


def test_oas31_null_type_array_detected(base_spec):
    """OAS 3.1 style type arrays containing 'null' are treated as nullable."""
    old = {
        **base_spec,
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": ["string", "null"]},
                    }
                }
            }
        },
    }
    new = {
        **base_spec,
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string"},  # null removed from array
                    }
                }
            }
        },
    }
    report = diff_nullable(old, new)
    assert len(report.changes) == 1
    assert report.changes[0].severity == Severity.BREAKING


def test_no_schemas_returns_empty_report():
    old = {"openapi": "3.0.3", "info": {"version": "1.0"}, "paths": {}}
    new = {"openapi": "3.0.3", "info": {"version": "2.0"}, "paths": {}}
    report = diff_nullable(old, new)
    assert report.changes == []


def test_path_format_is_correct(base_spec):
    new_spec = {
        **base_spec,
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "nickname": {"type": "string"},
                    },
                }
            }
        },
    }
    report = diff_nullable(base_spec, new_spec)
    assert report.changes[0].path == "#/components/schemas/User/properties/nickname"
