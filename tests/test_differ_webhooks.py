"""Tests for apidiff.differ_webhooks."""
import pytest
from apidiff.differ import ChangeType, Severity
from apidiff.differ_webhooks import diff_webhooks


@pytest.fixture()
def base_spec() -> dict:
    return {
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {},
        "webhooks": {
            "newOrder": {
                "post": {
                    "requestBody": {"content": {}},
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    report = diff_webhooks(base_spec, base_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = {**base_spec, "info": {"title": "Test", "version": "2.0.0"}}
    report = diff_webhooks(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_webhook_is_breaking(base_spec):
    new_spec = {**base_spec, "webhooks": {}}
    report = diff_webhooks(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert change.change_type == ChangeType.REMOVED
    assert "newOrder" in change.path


def test_added_webhook_is_non_breaking(base_spec):
    new_spec = {
        **base_spec,
        "webhooks": {
            **base_spec["webhooks"],
            "cancelOrder": {"post": {"responses": {"200": {"description": "OK"}}}},
        },
    }
    report = diff_webhooks(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.NON_BREAKING
    assert change.change_type == ChangeType.ADDED
    assert "cancelOrder" in change.path


def test_removed_operation_from_webhook_is_breaking(base_spec):
    new_spec = {**base_spec, "webhooks": {"newOrder": {}}}
    report = diff_webhooks(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert "post" in change.path


def test_added_operation_to_webhook_is_non_breaking(base_spec):
    new_spec = {
        **base_spec,
        "webhooks": {
            "newOrder": {
                **base_spec["webhooks"]["newOrder"],
                "get": {"responses": {"200": {"description": "OK"}}},
            }
        },
    }
    report = diff_webhooks(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.NON_BREAKING
    assert "get" in change.path


def test_empty_webhooks_both_sides():
    spec = {"openapi": "3.1.0", "info": {"title": "T", "version": "1.0"}, "paths": {}}
    report = diff_webhooks(spec, spec)
    assert report.changes == []
