"""Tests for apidiff.differ_security."""

import pytest
from apidiff.differ_security import diff_security
from apidiff.differ import Severity, ChangeType


@pytest.fixture
def base_spec():
    return {
        "info": {"version": "1.0.0"},
        "components": {
            "securitySchemes": {
                "BearerAuth": {"type": "http", "scheme": "bearer"},
                "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
            }
        },
        "security": [{"BearerAuth": []}],
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_security(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = dict(base_spec)
    new_spec["info"] = {"version": "2.0.0"}
    report = diff_security(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_scheme_is_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": {
            "securitySchemes": {
                "BearerAuth": {"type": "http", "scheme": "bearer"},
            }
        },
        "security": [{"BearerAuth": []}],
    }
    report = diff_security(base_spec, new_spec)
    removed = [c for c in report.changes if c.change_type == ChangeType.REMOVED]
    assert any("ApiKeyAuth" in c.description for c in removed)
    assert all(c.severity == Severity.BREAKING for c in removed)


def test_added_scheme_is_non_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": {
            "securitySchemes": {
                "BearerAuth": {"type": "http", "scheme": "bearer"},
                "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
                "OAuth2": {"type": "oauth2"},
            }
        },
        "security": [{"BearerAuth": []}],
    }
    report = diff_security(base_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED]
    assert any("OAuth2" in c.description for c in added)
    assert all(c.severity == Severity.NON_BREAKING for c in added)


def test_scheme_type_change_is_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": {
            "securitySchemes": {
                "BearerAuth": {"type": "apiKey", "in": "header", "name": "Authorization"},
                "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
            }
        },
        "security": [{"BearerAuth": []}],
    }
    report = diff_security(base_spec, new_spec)
    modified = [c for c in report.changes if c.change_type == ChangeType.MODIFIED]
    assert len(modified) == 1
    assert modified[0].severity == Severity.BREAKING
    assert "BearerAuth" in modified[0].description


def test_removed_global_security_is_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": base_spec["components"],
        "security": [],
    }
    report = diff_security(base_spec, new_spec)
    removed = [
        c for c in report.changes
        if c.change_type == ChangeType.REMOVED and c.path == "#/security"
    ]
    assert len(removed) == 1
    assert removed[0].severity == Severity.BREAKING


def test_added_global_security_is_non_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "components": base_spec["components"],
        "security": [{"BearerAuth": []}, {"ApiKeyAuth": []}],
    }
    report = diff_security(base_spec, new_spec)
    added = [
        c for c in report.changes
        if c.change_type == ChangeType.ADDED and c.path == "#/security"
    ]
    assert len(added) == 1
    assert added[0].severity == Severity.NON_BREAKING
