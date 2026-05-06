"""Tests for apidiff.differ_info."""

import pytest
from apidiff.differ import ChangeType, Severity
from apidiff.differ_info import diff_info


@pytest.fixture
def base_spec():
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "My API",
            "version": "1.0.0",
            "description": "A sample API",
            "termsOfService": "https://example.com/tos",
        },
        "paths": {},
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_info(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    report = diff_info(base_spec, base_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "1.0.0"


def test_title_change_is_non_breaking(base_spec):
    new_spec = {**base_spec, "info": {**base_spec["info"], "title": "New API Name"}}
    report = diff_info(base_spec, new_spec)
    title_changes = [c for c in report.changes if c.path == "info.title"]
    assert len(title_changes) == 1
    assert title_changes[0].severity == Severity.NON_BREAKING
    assert title_changes[0].change_type == ChangeType.MODIFIED


def test_version_change_is_non_breaking(base_spec):
    new_spec = {**base_spec, "info": {**base_spec["info"], "version": "2.0.0"}}
    report = diff_info(base_spec, new_spec)
    version_changes = [c for c in report.changes if c.path == "info.version"]
    assert len(version_changes) == 1
    assert version_changes[0].severity == Severity.NON_BREAKING


def test_removed_field_is_detected(base_spec):
    new_info = {k: v for k, v in base_spec["info"].items() if k != "description"}
    new_spec = {**base_spec, "info": new_info}
    report = diff_info(base_spec, new_spec)
    removed = [c for c in report.changes if c.path == "info.description"]
    assert len(removed) == 1
    assert removed[0].change_type == ChangeType.REMOVED


def test_added_field_is_detected(base_spec):
    new_spec = {**base_spec, "info": {**base_spec["info"], "license": {"name": "MIT"}}}
    report = diff_info(base_spec, new_spec)
    added = [c for c in report.changes if c.path == "info.license"]
    assert len(added) == 1
    assert added[0].change_type == ChangeType.ADDED


def test_description_in_change_text(base_spec):
    new_spec = {**base_spec, "info": {**base_spec["info"], "title": "Renamed"}}
    report = diff_info(base_spec, new_spec)
    title_change = next(c for c in report.changes if c.path == "info.title")
    assert "My API" in title_change.description
    assert "Renamed" in title_change.description


def test_operation_is_none_for_info_changes(base_spec):
    new_spec = {**base_spec, "info": {**base_spec["info"], "version": "3.0.0"}}
    report = diff_info(base_spec, new_spec)
    for change in report.changes:
        assert change.operation is None


def test_unknown_field_change_is_non_breaking(base_spec):
    new_spec = {**base_spec, "info": {**base_spec["info"], "x-custom": "value"}}
    report = diff_info(base_spec, new_spec)
    custom = [c for c in report.changes if c.path == "info.x-custom"]
    assert len(custom) == 1
    assert custom[0].severity == Severity.NON_BREAKING
