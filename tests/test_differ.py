"""Tests for the core diffing module."""

import pytest
from apidiff.differ import (
    ChangeType,
    DiffReport,
    Severity,
    diff_specs,
)


@pytest.fixture
def base_spec():
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "listUsers",
                    "parameters": [
                        {"name": "limit", "in": "query", "required": False}
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/users/{id}": {
                "get": {
                    "operationId": "getUser",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True}
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            },
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_specs(base_spec, base_spec)
    assert isinstance(report, DiffReport)
    assert len(report.changes) == 0
    assert not report.has_breaking_changes


def test_removed_path_is_breaking(base_spec):
    new_spec = dict(base_spec)
    new_spec["paths"] = {"/users": base_spec["paths"]["/users"]}
    report = diff_specs(base_spec, new_spec)
    breaking = report.breaking_changes
    assert any("/users/{id}" in c.path for c in breaking)
    assert any(c.change_type == ChangeType.REMOVED for c in breaking)


def test_added_path_is_non_breaking(base_spec):
    new_spec = dict(base_spec)
    new_spec["paths"] = {
        **base_spec["paths"],
        "/posts": {"get": {"responses": {"200": {"description": "OK"}}}},
    }
    report = diff_specs(base_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED]
    assert any("/posts" in c.path for c in added)
    assert all(c.severity == Severity.NON_BREAKING for c in added if "/posts" in c.path)


def test_removed_operation_is_breaking(base_spec):
    new_spec = {
        **base_spec,
        "paths": {
            "/users": {},
            "/users/{id}": base_spec["paths"]["/users/{id}"],
        },
    }
    report = diff_specs(base_spec, new_spec)
    assert any(
        "get" in c.path and "/users" in c.path and c.severity == Severity.BREAKING
        for c in report.changes
    )


def test_parameter_removed_is_breaking(base_spec):
    new_spec = {
        **base_spec,
        "paths": {
            "/users": {
                "get": {
                    "operationId": "listUsers",
                    "parameters": [],
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/users/{id}": base_spec["paths"]["/users/{id}"],
        },
    }
    report = diff_specs(base_spec, new_spec)
    assert any(
        "limit" in c.path and c.severity == Severity.BREAKING for c in report.changes
    )


def test_parameter_became_required_is_breaking(base_spec):
    new_spec = {
        **base_spec,
        "paths": {
            "/users": {
                "get": {
                    "operationId": "listUsers",
                    "parameters": [
                        {"name": "limit", "in": "query", "required": True}
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/users/{id}": base_spec["paths"]["/users/{id}"],
        },
    }
    report = diff_specs(base_spec, new_spec)
    assert any(
        "limit" in c.path and c.severity == Severity.BREAKING for c in report.changes
    )


def test_version_change_is_info(base_spec):
    new_spec = {
        **base_spec,
        "info": {"title": "Test API", "version": "2.0.0"},
    }
    report = diff_specs(base_spec, new_spec)
    version_changes = [c for c in report.changes if "version" in c.path]
    assert len(version_changes) == 1
    assert version_changes[0].severity == Severity.INFO
    assert version_changes[0].old_value == "1.0.0"
    assert version_changes[0].new_value == "2.0.0"


def test_summary_counts(base_spec):
    new_spec = {
        **base_spec,
        "paths": {
            "/posts": {"get": {"responses": {"200": {"description": "OK"}}}},
        },
    }
    report = diff_specs(base_spec, new_spec)
    summary = report.summary()
    assert summary["total"] == len(report.changes)
    assert summary["breaking"] == len(report.breaking_changes)
    assert summary["breaking"] + summary["non_breaking"] + summary["info"] == summary["total"]
