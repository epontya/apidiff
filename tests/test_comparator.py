"""Tests for apidiff.comparator schema field comparison."""

import pytest
from apidiff.comparator import compare_schemas, FieldDiff
from apidiff.differ import ChangeType, Severity


OLD_SCHEMA = {
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string"},
    },
    "required": ["id", "name"],
}

NEW_SCHEMA_REMOVED_REQUIRED = {
    "properties": {
        "id": {"type": "integer"},
    },
    "required": ["id"],
}

NEW_SCHEMA_ADDED_OPTIONAL = {
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": "string"},
    },
    "required": ["id", "name"],
}

NEW_SCHEMA_TYPE_CHANGED = {
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "email": {"type": "string"},
    },
    "required": ["id", "name"],
}


def test_no_changes_returns_empty():
    diffs = compare_schemas("/users", OLD_SCHEMA, OLD_SCHEMA)
    assert diffs == []


def test_removed_required_field_is_breaking():
    diffs = compare_schemas("/users", OLD_SCHEMA, NEW_SCHEMA_REMOVED_REQUIRED)
    removed = [d for d in diffs if d.field_name == "name" and d.change_type == ChangeType.REMOVED]
    assert len(removed) == 1
    assert removed[0].severity == Severity.BREAKING


def test_removed_optional_field_is_non_breaking():
    diffs = compare_schemas("/users", OLD_SCHEMA, NEW_SCHEMA_REMOVED_REQUIRED)
    removed = [d for d in diffs if d.field_name == "email" and d.change_type == ChangeType.REMOVED]
    assert len(removed) == 1
    assert removed[0].severity == Severity.NON_BREAKING


def test_added_optional_field_is_non_breaking():
    diffs = compare_schemas("/users", OLD_SCHEMA, NEW_SCHEMA_ADDED_OPTIONAL)
    added = [d for d in diffs if d.field_name == "phone" and d.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].severity == Severity.NON_BREAKING


def test_added_required_field_is_breaking():
    schema_with_new_required = {
        "properties": {**OLD_SCHEMA["properties"], "token": {"type": "string"}},
        "required": ["id", "name", "token"],
    }
    diffs = compare_schemas("/users", OLD_SCHEMA, schema_with_new_required)
    added = [d for d in diffs if d.field_name == "token" and d.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].severity == Severity.BREAKING


def test_type_change_is_breaking():
    diffs = compare_schemas("/users", OLD_SCHEMA, NEW_SCHEMA_TYPE_CHANGED)
    modified = [d for d in diffs if d.field_name == "id" and d.change_type == ChangeType.MODIFIED]
    assert len(modified) == 1
    assert modified[0].severity == Severity.BREAKING
    assert modified[0].old_value == "integer"
    assert modified[0].new_value == "string"


def test_field_diff_to_change_sets_path():
    diffs = compare_schemas("/items", OLD_SCHEMA, NEW_SCHEMA_REMOVED_REQUIRED)
    change = diffs[0].to_change(operation="get", method="GET")
    assert change.path == "/items"


def test_field_diff_description_contains_field_name():
    diffs = compare_schemas("/users", OLD_SCHEMA, NEW_SCHEMA_REMOVED_REQUIRED)
    removed = [d for d in diffs if d.field_name == "name"]
    assert "name" in removed[0].to_change().description
