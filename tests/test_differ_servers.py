"""Tests for apidiff.differ_servers."""

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_servers import diff_servers


@pytest.fixture()
def base_spec() -> dict:
    return {
        "info": {"title": "API", "version": "1.0.0"},
        "paths": {},
        "servers": [
            {"url": "https://api.example.com/v1", "description": "Production"},
            {"url": "https://staging.example.com/v1", "description": "Staging"},
        ],
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_servers(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = {**base_spec, "info": {"title": "API", "version": "2.0.0"}}
    report = diff_servers(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_server_is_breaking(base_spec):
    new_spec = {
        **base_spec,
        "servers": [{"url": "https://api.example.com/v1", "description": "Production"}],
    }
    report = diff_servers(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert len(breaking) == 1
    assert "staging.example.com" in breaking[0].path


def test_removed_server_change_type_is_removed(base_spec):
    new_spec = {
        **base_spec,
        "servers": [{"url": "https://api.example.com/v1"}],
    }
    report = diff_servers(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert breaking[0].change_type == ChangeType.REMOVED


def test_added_server_is_non_breaking(base_spec):
    new_spec = {
        **base_spec,
        "servers": [
            {"url": "https://api.example.com/v1", "description": "Production"},
            {"url": "https://staging.example.com/v1", "description": "Staging"},
            {"url": "https://sandbox.example.com/v1", "description": "Sandbox"},
        ],
    }
    report = diff_servers(base_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].severity == Severity.NON_BREAKING
    assert "sandbox.example.com" in added[0].path


def test_description_change_is_non_breaking(base_spec):
    new_spec = {
        **base_spec,
        "servers": [
            {"url": "https://api.example.com/v1", "description": "Live Production"},
            {"url": "https://staging.example.com/v1", "description": "Staging"},
        ],
    }
    report = diff_servers(base_spec, new_spec)
    modified = [c for c in report.changes if c.change_type == ChangeType.MODIFIED]
    assert len(modified) == 1
    assert modified[0].severity == Severity.NON_BREAKING
    assert "description" in modified[0].path


def test_empty_servers_list_no_changes():
    spec = {"info": {"title": "API", "version": "1.0.0"}, "paths": {}}
    report = diff_servers(spec, spec)
    assert report.changes == []


def test_all_servers_removed_all_breaking(base_spec):
    new_spec = {**base_spec, "servers": []}
    report = diff_servers(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert len(breaking) == 2
