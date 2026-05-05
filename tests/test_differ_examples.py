"""Tests for apidiff.differ_examples."""

from __future__ import annotations

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_examples import diff_examples


@pytest.fixture()
def base_spec() -> dict:
    return {
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "examples": {
                                        "UserExample": {
                                            "value": {"id": 1, "name": "Alice"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "examples": {
                "PetExample": {"value": {"id": 42, "name": "Fido"}},
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_examples(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    report = diff_examples(base_spec, base_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "1.0.0"


def test_removed_named_example_is_non_breaking(base_spec):
    new_spec = {**base_spec, "components": {"examples": {}}}
    report = diff_examples(base_spec, new_spec)
    assert any(
        c.change_type == ChangeType.REMOVED and c.severity == Severity.NON_BREAKING
        for c in report.changes
    )


def test_added_named_example_is_non_breaking(base_spec):
    new_spec = {
        **base_spec,
        "components": {
            "examples": {
                **base_spec["components"]["examples"],
                "NewExample": {"value": {"x": 1}},
            }
        },
    }
    report = diff_examples(base_spec, new_spec)
    assert any(
        c.change_type == ChangeType.ADDED and c.severity == Severity.NON_BREAKING
        for c in report.changes
    )


def test_modified_named_example_is_non_breaking(base_spec):
    new_spec = {
        **base_spec,
        "components": {
            "examples": {
                "PetExample": {"value": {"id": 99, "name": "Rex"}},
            }
        },
    }
    report = diff_examples(base_spec, new_spec)
    assert any(
        c.change_type == ChangeType.MODIFIED and c.severity == Severity.NON_BREAKING
        for c in report.changes
    )


def test_removed_inline_example_is_non_breaking(base_spec):
    import copy

    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["examples"] = {}
    report = diff_examples(base_spec, new_spec)
    assert any(
        c.change_type == ChangeType.REMOVED and "UserExample" in c.path
        for c in report.changes
    )


def test_modified_inline_example_is_non_breaking(base_spec):
    import copy

    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["examples"]["UserExample"] = {"value": {"id": 2, "name": "Bob"}}
    report = diff_examples(base_spec, new_spec)
    assert any(
        c.change_type == ChangeType.MODIFIED and c.severity == Severity.NON_BREAKING
        for c in report.changes
    )


def test_all_changes_are_non_breaking(base_spec):
    new_spec = {
        **base_spec,
        "components": {"examples": {}},
    }
    report = diff_examples(base_spec, new_spec)
    assert all(c.severity == Severity.NON_BREAKING for c in report.changes)


def test_named_example_path_contains_components(base_spec):
    new_spec = {**base_spec, "components": {"examples": {}}}
    report = diff_examples(base_spec, new_spec)
    removed = [c for c in report.changes if c.change_type == ChangeType.REMOVED]
    assert any("#/components/examples" in c.path for c in removed)
