"""Integration tests: comparator feeds Changes into DiffReport."""

import pytest
from apidiff.comparator import compare_schemas
from apidiff.differ import DiffReport, Severity, ChangeType


OLD_SCHEMA = {
    "properties": {
        "id": {"type": "integer"},
        "username": {"type": "string"},
        "role": {"type": "string"},
    },
    "required": ["id", "username"],
}

NEW_SCHEMA_ROLE_REMOVED = {
    "properties": {
        "id": {"type": "integer"},
        "username": {"type": "string"},
    },
    "required": ["id", "username"],
}

NEW_SCHEMA_ID_TYPE_CHANGED = {
    "properties": {
        "id": {"type": "string"},
        "username": {"type": "string"},
        "role": {"type": "string"},
    },
    "required": ["id", "username"],
}


def _build_report(old, new, path="/users") -> DiffReport:
    diffs = compare_schemas(path, old, new)
    changes = [d.to_change(operation="post") for d in diffs]
    return DiffReport(old_version="1.0", new_version="2.0", changes=changes)


def test_optional_removal_produces_non_breaking_report():
    report = _build_report(OLD_SCHEMA, NEW_SCHEMA_ROLE_REMOVED)
    assert len(report.changes) == 1
    assert report.changes[0].severity == Severity.NON_BREAKING


def test_type_change_produces_breaking_report():
    report = _build_report(OLD_SCHEMA, NEW_SCHEMA_ID_TYPE_CHANGED)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert len(breaking) == 1


def test_report_change_type_is_modified_for_type_change():
    report = _build_report(OLD_SCHEMA, NEW_SCHEMA_ID_TYPE_CHANGED)
    modified = [c for c in report.changes if c.change_type == ChangeType.MODIFIED]
    assert len(modified) == 1


def test_report_versions_preserved():
    report = _build_report(OLD_SCHEMA, NEW_SCHEMA_ROLE_REMOVED)
    assert report.old_version == "1.0"
    assert report.new_version == "2.0"


def test_no_schema_changes_produces_empty_report():
    report = _build_report(OLD_SCHEMA, OLD_SCHEMA)
    assert report.changes == []


def test_change_path_is_set_correctly():
    report = _build_report(OLD_SCHEMA, NEW_SCHEMA_ROLE_REMOVED, path="/accounts")
    assert report.changes[0].path == "/accounts"
