"""Tests for apidiff.differ_enums."""

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_enums import diff_enums


@pytest.fixture
def base_spec() -> dict:
    return {
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "Status": {
                    "type": "string",
                    "enum": ["active", "inactive", "pending"],
                },
                "Role": {
                    "type": "string",
                    "enum": ["admin", "user"],
                },
            }
        },
        "paths": {
            "/items": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "string",
                                        "enum": ["foo", "bar"],
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_enums(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = dict(base_spec)
    new_spec["info"] = {"version": "2.0.0"}
    report = diff_enums(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_enum_value_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Status"]["enum"] = ["active", "inactive"]
    report = diff_enums(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert len(breaking) == 1
    assert "pending" in breaking[0].description


def test_added_enum_value_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Status"]["enum"] = [
        "active", "inactive", "pending", "archived"
    ]
    report = diff_enums(base_spec, new_spec)
    non_breaking = [c for c in report.changes if c.severity == Severity.NON_BREAKING]
    assert len(non_breaking) == 1
    assert "archived" in non_breaking[0].description


def test_removed_enum_change_type_is_removed(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Role"]["enum"] = ["admin"]
    report = diff_enums(base_spec, new_spec)
    removed = [c for c in report.changes if c.change_type == ChangeType.REMOVED]
    assert any("user" in c.description for c in removed)


def test_inline_enum_removal_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/items"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["enum"] = ["foo"]
    report = diff_enums(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert len(breaking) == 1
    assert "bar" in breaking[0].description


def test_inline_enum_addition_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/items"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["enum"] = ["foo", "bar", "baz"]
    report = diff_enums(base_spec, new_spec)
    non_breaking = [c for c in report.changes if c.severity == Severity.NON_BREAKING]
    assert any("baz" in c.description for c in non_breaking)


def test_schema_without_enum_ignored(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["NoEnum"] = {"type": "string"}
    report = diff_enums(base_spec, new_spec)
    paths = [c.path for c in report.changes]
    assert not any("NoEnum" in p for p in paths)
