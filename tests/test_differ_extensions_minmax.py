"""Tests for differ_extensions_minmax — min/max constraint change detection."""

import pytest
from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_minmax import diff_minmax


@pytest.fixture
def base_spec():
    return {
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "Widget": {
                    "properties": {
                        "count": {"type": "integer", "minimum": 0, "maximum": 100},
                        "score": {"type": "number", "minimum": 0.0},
                    }
                }
            }
        },
    }


def _new_spec(props):
    return {
        "info": {"version": "2.0.0"},
        "components": {"schemas": {"Widget": {"properties": props}}},
    }


def test_no_changes_returns_empty_report(base_spec):
    new = _new_spec({"count": {"type": "integer", "minimum": 0, "maximum": 100}, "score": {"type": "number", "minimum": 0.0}})
    report = diff_minmax(base_spec, new)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new = _new_spec({"count": {"type": "integer", "minimum": 0, "maximum": 100}, "score": {"type": "number", "minimum": 0.0}})
    report = diff_minmax(base_spec, new)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_raised_minimum_is_breaking(base_spec):
    new = _new_spec({"count": {"type": "integer", "minimum": 5, "maximum": 100}, "score": {"type": "number", "minimum": 0.0}})
    report = diff_minmax(base_spec, new)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert len(breaking) == 1
    assert "minimum" in breaking[0].description
    assert breaking[0].change_type == ChangeType.MODIFIED


def test_lowered_minimum_is_non_breaking(base_spec):
    new = _new_spec({"count": {"type": "integer", "minimum": -10, "maximum": 100}, "score": {"type": "number", "minimum": 0.0}})
    report = diff_minmax(base_spec, new)
    non_breaking = [c for c in report.changes if c.severity == Severity.NON_BREAKING]
    assert len(non_breaking) == 1
    assert "minimum" in non_breaking[0].description


def test_lowered_maximum_is_breaking(base_spec):
    new = _new_spec({"count": {"type": "integer", "minimum": 0, "maximum": 50}, "score": {"type": "number", "minimum": 0.0}})
    report = diff_minmax(base_spec, new)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert len(breaking) == 1
    assert "maximum" in breaking[0].description


def test_raised_maximum_is_non_breaking(base_spec):
    new = _new_spec({"count": {"type": "integer", "minimum": 0, "maximum": 200}, "score": {"type": "number", "minimum": 0.0}})
    report = diff_minmax(base_spec, new)
    non_breaking = [c for c in report.changes if c.severity == Severity.NON_BREAKING]
    assert len(non_breaking) == 1
    assert "maximum" in non_breaking[0].description


def test_adding_minimum_where_none_existed_is_breaking():
    old = {
        "info": {"version": "1.0.0"},
        "components": {"schemas": {"Item": {"properties": {"qty": {"type": "integer"}}}}},
    }
    new = {
        "info": {"version": "2.0.0"},
        "components": {"schemas": {"Item": {"properties": {"qty": {"type": "integer", "minimum": 1}}}}},
    }
    report = diff_minmax(old, new)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert len(breaking) == 1


def test_path_contains_schema_and_property(base_spec):
    new = _new_spec({"count": {"type": "integer", "minimum": 10, "maximum": 100}, "score": {"type": "number", "minimum": 0.0}})
    report = diff_minmax(base_spec, new)
    assert any("Widget" in c.path and "count" in c.path for c in report.changes)
