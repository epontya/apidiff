"""Tests for allOf / anyOf / oneOf composition diffing."""
import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_allof import diff_allof


@pytest.fixture()
def base_spec():
    return {
        "info": {"title": "API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Pet": {
                    "allOf": [
                        {"$ref": "#/components/schemas/Animal"},
                        {"type": "object"},
                    ],
                    "anyOf": [
                        {"$ref": "#/components/schemas/Cat"},
                        {"$ref": "#/components/schemas/Dog"},
                    ],
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_allof(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new = dict(base_spec)
    new["info"] = {"title": "API", "version": "2.0.0"}
    report = diff_allof(base_spec, new)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_allof_member_is_breaking(base_spec):
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Pet": {
                    "allOf": [
                        {"$ref": "#/components/schemas/Animal"},
                        # type:object removed
                    ],
                    "anyOf": [
                        {"$ref": "#/components/schemas/Cat"},
                        {"$ref": "#/components/schemas/Dog"},
                    ],
                }
            }
        },
    }
    report = diff_allof(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert len(breaking) == 1
    assert breaking[0].change_type == ChangeType.REMOVED
    assert "allOf" in breaking[0].path


def test_added_allof_member_is_breaking(base_spec):
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Pet": {
                    "allOf": [
                        {"$ref": "#/components/schemas/Animal"},
                        {"type": "object"},
                        {"$ref": "#/components/schemas/Extra"},  # new
                    ],
                    "anyOf": [
                        {"$ref": "#/components/schemas/Cat"},
                        {"$ref": "#/components/schemas/Dog"},
                    ],
                }
            }
        },
    }
    report = diff_allof(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert any(c.change_type == ChangeType.ADDED for c in breaking)


def test_added_anyof_member_is_non_breaking(base_spec):
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Pet": {
                    "allOf": [
                        {"$ref": "#/components/schemas/Animal"},
                        {"type": "object"},
                    ],
                    "anyOf": [
                        {"$ref": "#/components/schemas/Cat"},
                        {"$ref": "#/components/schemas/Dog"},
                        {"$ref": "#/components/schemas/Bird"},  # new
                    ],
                }
            }
        },
    }
    report = diff_allof(base_spec, new_spec)
    non_breaking = [
        c for c in report.changes if c.severity == Severity.NON_BREAKING
    ]
    assert len(non_breaking) == 1
    assert "anyOf" in non_breaking[0].path


def test_removed_anyof_member_is_breaking(base_spec):
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Pet": {
                    "allOf": [
                        {"$ref": "#/components/schemas/Animal"},
                        {"type": "object"},
                    ],
                    "anyOf": [
                        {"$ref": "#/components/schemas/Cat"},
                        # Dog removed
                    ],
                }
            }
        },
    }
    report = diff_allof(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert any("anyOf" in c.path for c in breaking)
