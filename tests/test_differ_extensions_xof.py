"""Tests for oneOf/anyOf composition differ."""
import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_xof import diff_xof


@pytest.fixture()
def base_spec() -> dict:
    return {
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "Pet": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/Cat"},
                        {"$ref": "#/components/schemas/Dog"},
                    ]
                },
                "Result": {
                    "anyOf": [
                        {"$ref": "#/components/schemas/Success"},
                        {"$ref": "#/components/schemas/Error"},
                    ]
                },
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_xof(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = dict(base_spec)
    new_spec["info"] = {"version": "2.0.0"}
    report = diff_xof(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_oneof_member_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Pet"]["oneOf"] = [
        {"$ref": "#/components/schemas/Cat"}
    ]
    report = diff_xof(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert len(breaking) == 1
    assert "Dog" in breaking[0].description


def test_removed_oneof_member_change_type(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Pet"]["oneOf"] = [
        {"$ref": "#/components/schemas/Cat"}
    ]
    report = diff_xof(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert breaking[0].change_type == ChangeType.REMOVED


def test_added_oneof_member_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Pet"]["oneOf"].append(
        {"$ref": "#/components/schemas/Bird"}
    )
    report = diff_xof(base_spec, new_spec)
    non_breaking = [c for c in report.changes if c.severity == Severity.NON_BREAKING]
    assert len(non_breaking) == 1
    assert "Bird" in non_breaking[0].description


def test_removed_anyof_member_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Result"]["anyOf"] = [
        {"$ref": "#/components/schemas/Success"}
    ]
    report = diff_xof(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert any("Error" in c.description for c in breaking)


def test_path_contains_keyword(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Pet"]["oneOf"] = [
        {"$ref": "#/components/schemas/Cat"}
    ]
    report = diff_xof(base_spec, new_spec)
    assert any("oneOf" in c.path for c in report.changes)


def test_no_schemas_returns_empty_report():
    old = {"info": {"version": "1.0.0"}}
    new = {"info": {"version": "2.0.0"}}
    report = diff_xof(old, new)
    assert report.changes == []
