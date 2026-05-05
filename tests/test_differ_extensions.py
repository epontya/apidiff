"""Tests for apidiff/differ_extensions.py."""

import pytest
from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions import diff_request_response_schemas


@pytest.fixture
def base_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    },
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_request_response_schemas(base_spec, base_spec, "1.0", "1.1")
    assert report.changes == []


def test_report_versions_are_set(base_spec):
    report = diff_request_response_schemas(base_spec, base_spec, "1.0", "2.0")
    assert report.old_version == "1.0"
    assert report.new_version == "2.0"


def test_request_body_type_change_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["post"]["requestBody"]["content"]["application/json"]["schema"]["type"] = "array"
    report = diff_request_response_schemas(base_spec, new_spec, "1.0", "2.0")
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert change.change_type == ChangeType.MODIFIED
    assert "request body" in change.description
    assert "object" in change.description
    assert "array" in change.description


def test_response_schema_type_change_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["type"] = "string"
    report = diff_request_response_schemas(base_spec, new_spec, "1.0", "2.0")
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert "response 200" in change.description


def test_both_schemas_changed_produces_two_changes(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["post"]["requestBody"]["content"]["application/json"]["schema"]["type"] = "array"
    new_spec["paths"]["/users"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["type"] = "string"
    report = diff_request_response_schemas(base_spec, new_spec, "1.0", "2.0")
    assert len(report.changes) == 2


def test_missing_schema_does_not_raise(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    del new_spec["paths"]["/users"]["post"]["requestBody"]
    report = diff_request_response_schemas(base_spec, new_spec, "1.0", "2.0")
    # No crash, no change detected for missing schema
    assert isinstance(report.changes, list)


def test_path_and_operation_recorded(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["post"]["requestBody"]["content"]["application/json"]["schema"]["type"] = "array"
    report = diff_request_response_schemas(base_spec, new_spec, "1.0", "2.0")
    change = report.changes[0]
    assert change.path == "/users"
    assert change.operation == "POST"
