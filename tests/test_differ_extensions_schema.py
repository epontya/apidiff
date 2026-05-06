"""Tests for apidiff.differ_extensions_schema."""

from __future__ import annotations

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_schema import diff_component_schemas


@pytest.fixture()
def base_spec() -> dict:
    return {
        "info": {"title": "API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "nullable": True,
                    "required": ["id"],
                    "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
                },
                "Error": {
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                },
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_component_schemas(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = {**base_spec, "info": {"title": "API", "version": "2.0.0"}}
    report = diff_component_schemas(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_schema_is_breaking(base_spec):
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {"schemas": {"Error": base_spec["components"]["schemas"]["Error"]}},
    }
    report = diff_component_schemas(base_spec, new_spec)
    assert any(
        c.change_type == ChangeType.REMOVED and c.severity == Severity.BREAKING
        for c in report.changes
    )


def test_removed_schema_path_is_correct(base_spec):
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {"schemas": {}},
    }
    report = diff_component_schemas(base_spec, new_spec)
    paths = [c.path for c in report.changes if c.change_type == ChangeType.REMOVED]
    assert "#/components/schemas/User" in paths


def test_added_schema_is_non_breaking(base_spec):
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                **base_spec["components"]["schemas"],
                "NewModel": {"type": "object"},
            }
        },
    }
    report = diff_component_schemas(base_spec, new_spec)
    assert any(
        c.change_type == ChangeType.ADDED and c.severity == Severity.NON_BREAKING
        for c in report.changes
    )


def test_type_change_is_breaking(base_spec):
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "User": {**base_spec["components"]["schemas"]["User"], "type": "string"},
                "Error": base_spec["components"]["schemas"]["Error"],
            }
        },
    }
    report = diff_component_schemas(base_spec, new_spec)
    assert any(
        c.change_type == ChangeType.MODIFIED and c.severity == Severity.BREAKING
        and "type changed" in c.description
        for c in report.changes
    )


def test_nullable_removed_is_breaking(base_spec):
    new_user = {**base_spec["components"]["schemas"]["User"]}
    new_user["nullable"] = False
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "User": new_user,
                "Error": base_spec["components"]["schemas"]["Error"],
            }
        },
    }
    report = diff_component_schemas(base_spec, new_spec)
    assert any(
        "no longer nullable" in c.description for c in report.changes
    )


def test_new_required_field_is_breaking(base_spec):
    new_user = {**base_spec["components"]["schemas"]["User"], "required": ["id", "name"]}
    new_spec = {
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "User": new_user,
                "Error": base_spec["components"]["schemas"]["Error"],
            }
        },
    }
    report = diff_component_schemas(base_spec, new_spec)
    assert any(
        "added required field" in c.description and c.severity == Severity.BREAKING
        for c in report.changes
    )


def test_no_components_section_returns_empty(base_spec):
    old = {"info": {"title": "API", "version": "1.0.0"}, "paths": {}}
    new = {"info": {"title": "API", "version": "2.0.0"}, "paths": {}}
    report = diff_component_schemas(old, new)
    assert report.changes == []
