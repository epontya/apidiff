"""Tests for differ_extensions_constraints."""
import pytest
from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_constraints import diff_constraints


@pytest.fixture
def base_spec():
    return {
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "Widget": {
                    "properties": {
                        "name": {"type": "string", "minLength": 1, "maxLength": 100},
                        "count": {"type": "integer", "minimum": 0, "maximum": 999},
                    }
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_constraints(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = dict(base_spec, info={"version": "2.0.0"})
    report = diff_constraints(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_tightened_min_length_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Widget"]["properties"]["name"]["minLength"] = 5
    report = diff_constraints(base_spec, new_spec)
    assert any(
        c.severity == Severity.BREAKING and "minLength" in c.path
        for c in report.changes
    )


def test_loosened_min_length_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Widget"]["properties"]["name"]["minLength"] = 0
    report = diff_constraints(base_spec, new_spec)
    assert any(
        c.severity == Severity.NON_BREAKING and "minLength" in c.path
        for c in report.changes
    )


def test_tightened_maximum_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Widget"]["properties"]["count"]["maximum"] = 10
    report = diff_constraints(base_spec, new_spec)
    assert any(
        c.severity == Severity.BREAKING and "maximum" in c.path
        for c in report.changes
    )


def test_removed_constraint_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    del new_spec["components"]["schemas"]["Widget"]["properties"]["name"]["maxLength"]
    report = diff_constraints(base_spec, new_spec)
    assert any(
        c.change_type == ChangeType.REMOVED and c.severity == Severity.NON_BREAKING
        for c in report.changes
    )


def test_added_tightening_constraint_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Widget"]["properties"]["count"]["minItems"] = 1
    report = diff_constraints(base_spec, new_spec)
    assert any(
        c.change_type == ChangeType.ADDED and c.severity == Severity.BREAKING
        for c in report.changes
    )


def test_path_contains_schema_and_property(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["components"]["schemas"]["Widget"]["properties"]["name"]["minLength"] = 10
    report = diff_constraints(base_spec, new_spec)
    assert any("Widget" in c.path and "name" in c.path for c in report.changes)


def test_skips_removed_schemas(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    del new_spec["components"]["schemas"]["Widget"]
    report = diff_constraints(base_spec, new_spec)
    assert report.changes == []
