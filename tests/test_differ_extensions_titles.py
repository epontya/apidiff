"""Tests for differ_extensions_titles module."""

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_titles import diff_titles


@pytest.fixture
def base_spec():
    return {
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "User": {
                    "title": "User Schema",
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "title": "User ID"},
                        "name": {"type": "string", "title": "Full Name"},
                    },
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_titles(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = dict(base_spec)
    new_spec["info"] = {"version": "2.0.0"}
    report = diff_titles(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_schema_title_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    del new_spec["components"]["schemas"]["User"]["title"]
    report = diff_titles(base_spec, new_spec)
    assert len(report.changes) == 1
    assert report.changes[0].severity == Severity.NON_BREAKING
    assert report.changes[0].change_type == ChangeType.REMOVED


def test_added_schema_title_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["User"]["title"] = "Updated User Schema"
    # Start from a spec with no title
    old_spec = copy.deepcopy(base_spec)
    del old_spec["components"]["schemas"]["User"]["title"]
    report = diff_titles(old_spec, new_spec)
    assert any(c.change_type == ChangeType.ADDED for c in report.changes)
    assert all(c.severity == Severity.NON_BREAKING for c in report.changes)


def test_modified_schema_title_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["User"]["title"] = "New Title"
    report = diff_titles(base_spec, new_spec)
    assert len(report.changes) == 1
    assert report.changes[0].change_type == ChangeType.MODIFIED
    assert report.changes[0].severity == Severity.NON_BREAKING


def test_removed_property_title_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    del new_spec["components"]["schemas"]["User"]["properties"]["id"]["title"]
    report = diff_titles(base_spec, new_spec)
    prop_changes = [
        c for c in report.changes if "properties/id" in c.path
    ]
    assert len(prop_changes) == 1
    assert prop_changes[0].severity == Severity.NON_BREAKING
    assert prop_changes[0].change_type == ChangeType.REMOVED


def test_modified_property_title_description_contains_names(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["User"]["properties"]["name"]["title"] = "Display Name"
    report = diff_titles(base_spec, new_spec)
    prop_changes = [
        c for c in report.changes if "properties/name" in c.path
    ]
    assert len(prop_changes) == 1
    assert "name" in prop_changes[0].description
    assert "User" in prop_changes[0].description


def test_no_schemas_returns_empty_report():
    old_spec = {"info": {"version": "1.0.0"}}
    new_spec = {"info": {"version": "2.0.0"}}
    report = diff_titles(old_spec, new_spec)
    assert report.changes == []


def test_path_contains_schema_name(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["User"]["title"] = "Changed"
    report = diff_titles(base_spec, new_spec)
    assert any("User" in c.path for c in report.changes)
