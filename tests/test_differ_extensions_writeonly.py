"""Tests for differ_extensions_writeonly."""
import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_writeonly import diff_writeonly


@pytest.fixture()
def base_spec():
    return {
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "password": {"type": "string", "writeOnly": True},
                        "name": {"type": "string"},
                    }
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_writeonly(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = dict(base_spec)
    new_spec["info"] = {"version": "2.0.0"}
    report = diff_writeonly(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_adding_writeonly_is_breaking(base_spec):
    import copy

    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["User"]["properties"]["name"]["writeOnly"] = True
    report = diff_writeonly(base_spec, new_spec)
    assert len(report.changes) == 1
    assert report.changes[0].severity == Severity.BREAKING


def test_removing_writeonly_is_non_breaking(base_spec):
    import copy

    new_spec = copy.deepcopy(base_spec)
    del new_spec["components"]["schemas"]["User"]["properties"]["password"]["writeOnly"]
    report = diff_writeonly(base_spec, new_spec)
    assert len(report.changes) == 1
    assert report.changes[0].severity == Severity.NON_BREAKING


def test_change_type_is_modified(base_spec):
    import copy

    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["User"]["properties"]["name"]["writeOnly"] = True
    report = diff_writeonly(base_spec, new_spec)
    assert report.changes[0].change_type == ChangeType.MODIFIED


def test_path_contains_schema_and_property(base_spec):
    import copy

    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["User"]["properties"]["name"]["writeOnly"] = True
    report = diff_writeonly(base_spec, new_spec)
    assert "User" in report.changes[0].path
    assert "name" in report.changes[0].path
    assert "writeOnly" in report.changes[0].path


def test_old_and_new_values_recorded(base_spec):
    import copy

    new_spec = copy.deepcopy(base_spec)
    del new_spec["components"]["schemas"]["User"]["properties"]["password"]["writeOnly"]
    report = diff_writeonly(base_spec, new_spec)
    change = report.changes[0]
    assert change.old_value == "True"
    assert change.new_value == "False"


def test_no_schemas_returns_empty_report():
    old = {"info": {"version": "1.0.0"}}
    new = {"info": {"version": "2.0.0"}}
    report = diff_writeonly(old, new)
    assert report.changes == []
