"""Tests for apidiff.differ_params — parameter-level diff detection."""

import pytest
from apidiff.differ import ChangeType, Severity
from apidiff.differ_params import diff_parameters


@pytest.fixture
def base_spec():
    return {
        "info": {"version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "parameters": [
                        {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                        {"name": "q", "in": "query", "required": False, "schema": {"type": "string"}},
                    ]
                }
            },
            "/users/{id}": {
                "get": {
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                    ]
                }
            },
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_parameters(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = {**base_spec, "info": {"version": "2.0.0"}}
    report = diff_parameters(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_required_param_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users/{id}"]["get"]["parameters"] = []
    report = diff_parameters(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert change.change_type == ChangeType.REMOVED
    assert "id" in change.description


def test_removed_optional_param_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    # remove 'q' which has required=False
    new_spec["paths"]["/users"]["get"]["parameters"] = [
        {"name": "limit", "in": "query", "schema": {"type": "integer"}}
    ]
    report = diff_parameters(base_spec, new_spec)
    assert any(
        c.severity == Severity.NON_BREAKING and "q" in c.description
        for c in report.changes
    )


def test_added_required_param_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["get"]["parameters"].append(
        {"name": "token", "in": "header", "required": True, "schema": {"type": "string"}}
    )
    report = diff_parameters(base_spec, new_spec)
    assert any(
        c.severity == Severity.BREAKING and "token" in c.description
        for c in report.changes
    )


def test_added_optional_param_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["get"]["parameters"].append(
        {"name": "sort", "in": "query", "required": False, "schema": {"type": "string"}}
    )
    report = diff_parameters(base_spec, new_spec)
    assert any(
        c.severity == Severity.NON_BREAKING and "sort" in c.description
        for c in report.changes
    )


def test_type_change_on_param_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["get"]["parameters"][0]["schema"]["type"] = "string"
    report = diff_parameters(base_spec, new_spec)
    assert any(
        c.severity == Severity.BREAKING
        and c.change_type == ChangeType.MODIFIED
        and "limit" in c.description
        for c in report.changes
    )


def test_skips_removed_paths(base_spec):
    """If a path is removed entirely, differ_params should not report param changes for it."""
    import copy
    new_spec = copy.deepcopy(base_spec)
    del new_spec["paths"]["/users/{id}"]
    report = diff_parameters(base_spec, new_spec)
    # Only changes from /users path (none in this case)
    assert all("/users/{id}" not in (c.path or "") for c in report.changes)
