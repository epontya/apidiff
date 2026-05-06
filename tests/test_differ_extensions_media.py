"""Tests for apidiff.differ_extensions_media."""

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_media import diff_media_types


@pytest.fixture()
def base_spec() -> dict:
    return {
        "info": {"version": "1.0.0"},
        "paths": {
            "/users": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {"schema": {"type": "object"}},
                            "application/xml": {"schema": {"type": "object"}},
                        }
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            }
                        }
                    },
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_media_types(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = {**base_spec, "info": {"version": "2.0.0"}}
    report = diff_media_types(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_request_media_type_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    del new_spec["paths"]["/users"]["post"]["requestBody"]["content"]["application/xml"]
    report = diff_media_types(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert len(breaking) == 1
    assert "application/xml" in breaking[0].description
    assert breaking[0].change_type == ChangeType.REMOVED


def test_added_request_media_type_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["post"]["requestBody"]["content"]["text/plain"] = {}
    report = diff_media_types(base_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED]
    assert any("text/plain" in c.description for c in added)
    assert all(c.severity == Severity.NON_BREAKING for c in added)


def test_removed_response_media_type_is_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    del new_spec["paths"]["/users"]["post"]["responses"]["200"]["content"]["application/json"]
    report = diff_media_types(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert any("application/json" in c.description for c in breaking)


def test_added_response_media_type_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["post"]["responses"]["200"]["content"]["application/xml"] = {}
    report = diff_media_types(base_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED]
    assert any("application/xml" in c.description for c in added)


def test_operation_field_set_correctly(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    del new_spec["paths"]["/users"]["post"]["requestBody"]["content"]["application/xml"]
    report = diff_media_types(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert breaking[0].operation == "POST"
    assert breaking[0].path == "/users"
