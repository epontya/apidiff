"""Tests for apidiff.differ_callbacks."""

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_callbacks import diff_callbacks


@pytest.fixture()
def base_spec() -> dict:
    return {
        "info": {"version": "1.0.0"},
        "paths": {
            "/orders": {
                "post": {
                    "operationId": "createOrder",
                    "callbacks": {
                        "orderStatus": {
                            "{$url}/order-status": {
                                "post": {"requestBody": {}, "responses": {"200": {}}}
                            }
                        }
                    },
                    "responses": {"201": {}},
                }
            }
        },
    }


def _new_spec(version: str, paths: dict) -> dict:
    return {"info": {"version": version}, "paths": paths}


def test_no_changes_returns_empty_report(base_spec):
    new_spec = {
        "info": {"version": "1.1.0"},
        "paths": base_spec["paths"],
    }
    report = diff_callbacks(base_spec, new_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = {"info": {"version": "2.0.0"}, "paths": base_spec["paths"]}
    report = diff_callbacks(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_callback_is_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "paths": {
            "/orders": {
                "post": {
                    "operationId": "createOrder",
                    "callbacks": {},
                    "responses": {"201": {}},
                }
            }
        },
    }
    report = diff_callbacks(base_spec, new_spec)
    assert len(report.changes) == 1
    change = report.changes[0]
    assert change.severity == Severity.BREAKING
    assert change.change_type == ChangeType.REMOVED
    assert "orderStatus" in change.path


def test_added_callback_is_non_breaking(base_spec):
    new_spec = {
        "info": {"version": "1.1.0"},
        "paths": {
            "/orders": {
                "post": {
                    "operationId": "createOrder",
                    "callbacks": {
                        "orderStatus": base_spec["paths"]["/orders"]["post"]["callbacks"]["orderStatus"],
                        "shipmentUpdate": {"{$url}/shipment": {"post": {"responses": {"200": {}}}}},
                    },
                    "responses": {"201": {}},
                }
            }
        },
    }
    report = diff_callbacks(base_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].severity == Severity.NON_BREAKING


def test_removed_expression_from_callback_is_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "paths": {
            "/orders": {
                "post": {
                    "operationId": "createOrder",
                    "callbacks": {"orderStatus": {}},
                    "responses": {"201": {}},
                }
            }
        },
    }
    report = diff_callbacks(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert any("{$url}/order-status" in c.path for c in breaking)


def test_no_paths_returns_empty_report():
    old = {"info": {"version": "1.0.0"}, "paths": {}}
    new = {"info": {"version": "1.1.0"}, "paths": {}}
    report = diff_callbacks(old, new)
    assert report.changes == []


def test_added_expression_to_callback_is_non_breaking(base_spec):
    old_cb = base_spec["paths"]["/orders"]["post"]["callbacks"]["orderStatus"]
    new_cb = dict(old_cb)
    new_cb["{$url}/order-cancel"] = {"post": {"responses": {"200": {}}}}
    new_spec = {
        "info": {"version": "1.1.0"},
        "paths": {
            "/orders": {
                "post": {
                    "callbacks": {"orderStatus": new_cb},
                    "responses": {"201": {}},
                }
            }
        },
    }
    report = diff_callbacks(base_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].severity == Severity.NON_BREAKING
