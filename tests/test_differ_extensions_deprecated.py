"""Tests for differ_extensions_deprecated and deprecated_cmd."""

import json
import textwrap
from pathlib import Path

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_deprecated import diff_deprecated_operations
from apidiff.deprecated_cmd import build_deprecated_parser, run_deprecated


@pytest.fixture
def base_spec():
    return {
        "info": {"title": "API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"summary": "List users", "deprecated": False},
                "post": {"summary": "Create user"},
            },
            "/items": {
                "get": {"summary": "List items", "deprecated": True},
            },
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_deprecated_operations(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = dict(base_spec)
    new_spec["info"] = {"title": "API", "version": "2.0.0"}
    report = diff_deprecated_operations(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_newly_deprecated_operation_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["get"]["deprecated"] = True
    report = diff_deprecated_operations(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.NON_BREAKING
    assert change.change_type == ChangeType.MODIFIED
    assert "/users" in change.path
    assert "deprecated" in change.description.lower()


def test_deprecation_removed_is_non_breaking(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/items"]["get"]["deprecated"] = False
    report = diff_deprecated_operations(base_spec, new_spec)
    assert len(report.changes) == 1
    assert report.changes[0].severity == Severity.NON_BREAKING


def test_added_operation_not_flagged(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/new"] = {"get": {"summary": "New", "deprecated": True}}
    report = diff_deprecated_operations(base_spec, new_spec)
    # New operation has no old counterpart — should not produce a change
    assert all(c.path != "/new" for c in report.changes)


def _write_spec(tmp_path: Path, name: str, spec: dict) -> str:
    p = tmp_path / name
    p.write_text(json.dumps(spec))
    return str(p)


def test_cmd_no_changes_returns_zero(tmp_path, base_spec):
    old = _write_spec(tmp_path, "old.json", base_spec)
    new = _write_spec(tmp_path, "new.json", base_spec)
    args = build_deprecated_parser().parse_args([old, new])
    assert run_deprecated(args) == 0


def test_cmd_with_changes_and_fail_flag_returns_one(tmp_path, base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["get"]["deprecated"] = True
    old = _write_spec(tmp_path, "old.json", base_spec)
    new = _write_spec(tmp_path, "new.json", new_spec)
    args = build_deprecated_parser().parse_args([old, new, "--fail-on-changes"])
    assert run_deprecated(args) == 1


def test_cmd_missing_file_returns_two(tmp_path, base_spec):
    old = _write_spec(tmp_path, "old.json", base_spec)
    args = build_deprecated_parser().parse_args([old, "nonexistent.json"])
    assert run_deprecated(args) == 2
