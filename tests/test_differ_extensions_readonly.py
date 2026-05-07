"""Tests for readOnly/writeOnly flag diffing."""

import pytest
from apidiff.differ import Severity, ChangeType
from apidiff.differ_extensions_readonly import diff_readonly


@pytest.fixture
def base_spec() -> dict:
    return {
        "info": {"title": "API", "version": "1.0.0"},
        "openapi": "3.0.0",
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "readOnly": True},
                        "password": {"type": "string", "writeOnly": True},
                        "name": {"type": "string"},
                    },
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_readonly(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    report = diff_readonly(base_spec, base_spec, old_version="1.0", new_version="2.0")
    assert report.old_version == "1.0"
    assert report.new_version == "2.0"


def test_adding_readonly_is_breaking(base_spec):
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "openapi": "3.0.0",
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "readOnly": True},
                        "password": {"type": "string", "writeOnly": True},
                        "name": {"type": "string", "readOnly": True},  # added
                    },
                }
            }
        },
    }
    report = diff_readonly(base_spec, new_spec)
    assert len(report.changes) == 1
    assert report.changes[0].severity == Severity.BREAKING
    assert "readOnly" in report.changes[0].path
    assert "name" in report.changes[0].path


def test_removing_readonly_is_non_breaking(base_spec):
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "openapi": "3.0.0",
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},  # readOnly removed
                        "password": {"type": "string", "writeOnly": True},
                        "name": {"type": "string"},
                    },
                }
            }
        },
    }
    report = diff_readonly(base_spec, new_spec)
    assert len(report.changes) == 1
    assert report.changes[0].severity == Severity.NON_BREAKING


def test_adding_writeonly_is_breaking(base_spec):
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "openapi": "3.0.0",
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "readOnly": True},
                        "password": {"type": "string", "writeOnly": True},
                        "name": {"type": "string", "writeOnly": True},  # added
                    },
                }
            }
        },
    }
    report = diff_readonly(base_spec, new_spec)
    assert len(report.changes) == 1
    assert report.changes[0].severity == Severity.BREAKING


def test_change_type_is_modified(base_spec):
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "openapi": "3.0.0",
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "readOnly": True},
                        "password": {"type": "string", "writeOnly": True},
                        "name": {"type": "string", "readOnly": True},
                    },
                }
            }
        },
    }
    report = diff_readonly(base_spec, new_spec)
    assert report.changes[0].change_type == ChangeType.MODIFIED


def test_no_schemas_returns_empty_report():
    old = {"info": {"title": "A", "version": "1"}, "openapi": "3.0.0", "paths": {}}
    new = {"info": {"title": "A", "version": "2"}, "openapi": "3.0.0", "paths": {}}
    report = diff_readonly(old, new)
    assert report.changes == []
