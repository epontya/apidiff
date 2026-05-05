"""Tests for apidiff.differ_links."""

from __future__ import annotations

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_links import diff_links


@pytest.fixture()
def base_spec() -> dict:
    return {
        "info": {"version": "1.0.0"},
        "paths": {
            "/users/{id}": {
                "get": {
                    "responses": {
                        "200": {
                            "links": {
                                "UserPosts": {
                                    "operationId": "listUserPosts",
                                    "parameters": {"userId": "$response.body#/id"},
                                }
                            }
                        }
                    }
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_links(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = {**base_spec, "info": {"version": "2.0.0"}}
    report = diff_links(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_link_is_non_breaking(base_spec):
    new_spec = {
        "info": {"version": "1.1.0"},
        "paths": {"/users/{id}": {"get": {"responses": {"200": {}}}}},
    }
    report = diff_links(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.NON_BREAKING
    assert change.change_type == ChangeType.REMOVED
    assert "UserPosts" in change.description


def test_added_link_is_non_breaking(base_spec):
    import copy

    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users/{id}"]["get"]["responses"]["200"]["links"]["UserOrders"] = {
        "operationId": "listUserOrders"
    }
    report = diff_links(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.NON_BREAKING
    assert change.change_type == ChangeType.ADDED


def test_changed_operation_id_is_breaking(base_spec):
    import copy

    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"]["/users/{id}"]["get"]["responses"]["200"]["links"]["UserPosts"][
        "operationId"
    ] = "getPostsByUser"
    report = diff_links(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert change.change_type == ChangeType.MODIFIED
    assert "operationId" in change.description


def test_changed_operation_ref_is_breaking(base_spec):
    import copy

    new_spec = copy.deepcopy(base_spec)
    link = new_spec["paths"]["/users/{id}"]["get"]["responses"]["200"]["links"]["UserPosts"]
    del link["operationId"]
    link["operationRef"] = "#/paths/~1users~1{id}/get"

    old_spec = copy.deepcopy(base_spec)
    old_link = old_spec["paths"]["/users/{id}"]["get"]["responses"]["200"]["links"]["UserPosts"]
    del old_link["operationId"]
    old_link["operationRef"] = "#/paths/~1posts/get"

    report = diff_links(old_spec, new_spec)
    assert any(
        c.severity == Severity.BREAKING and "operationRef" in c.description
        for c in report.changes
    )


def test_empty_specs_return_empty_report():
    old = {"info": {"version": "1.0.0"}, "paths": {}}
    new = {"info": {"version": "1.0.0"}, "paths": {}}
    report = diff_links(old, new)
    assert report.changes == []
