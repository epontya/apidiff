"""Tests for apidiff.differ_headers."""

import pytest
from apidiff.differ import ChangeType, Severity
from apidiff.differ_headers import diff_headers


@pytest.fixture
def base_spec():
    return {
        "info": {"version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "headers": {
                                "X-Rate-Limit": {
                                    "required": True,
                                    "schema": {"type": "integer"},
                                },
                                "X-Request-Id": {
                                    "required": False,
                                    "schema": {"type": "string"},
                                },
                            },
                        }
                    }
                }
            }
        },
    }


def test_no_changes_returns_empty_report(base_spec):
    new_spec = {"info": {"version": "1.1.0"}, "paths": base_spec["paths"]}
    report = diff_headers(base_spec, new_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    new_spec = {"info": {"version": "2.0.0"}, "paths": base_spec["paths"]}
    report = diff_headers(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_required_header_is_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {
                            "headers": {
                                "X-Request-Id": {"required": False, "schema": {"type": "string"}}
                            }
                        }
                    }
                }
            }
        },
    }
    report = diff_headers(base_spec, new_spec)
    removed = [c for c in report.changes if c.change_type == ChangeType.REMOVED and "X-Rate-Limit" in c.description]
    assert len(removed) == 1
    assert removed[0].severity == Severity.BREAKING


def test_removed_optional_header_is_non_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {
                            "headers": {
                                "X-Rate-Limit": {"required": True, "schema": {"type": "integer"}}
                            }
                        }
                    }
                }
            }
        },
    }
    report = diff_headers(base_spec, new_spec)
    removed = [c for c in report.changes if "X-Request-Id" in c.description]
    assert len(removed) == 1
    assert removed[0].severity == Severity.NON_BREAKING


def test_added_header_is_non_breaking(base_spec):
    new_paths = {
        "/users": {
            "get": {
                "responses": {
                    "200": {
                        "headers": {
                            **base_spec["paths"]["/users"]["get"]["responses"]["200"]["headers"],
                            "X-New-Header": {"schema": {"type": "string"}},
                        }
                    }
                }
            }
        }
    }
    new_spec = {"info": {"version": "1.1.0"}, "paths": new_paths}
    report = diff_headers(base_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].severity == Severity.NON_BREAKING


def test_header_type_change_is_breaking(base_spec):
    new_spec = {
        "info": {"version": "2.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "responses": {
                        "200": {
                            "headers": {
                                "X-Rate-Limit": {"required": True, "schema": {"type": "string"}},
                                "X-Request-Id": {"required": False, "schema": {"type": "string"}},
                            }
                        }
                    }
                }
            }
        },
    }
    report = diff_headers(base_spec, new_spec)
    modified = [c for c in report.changes if c.change_type == ChangeType.MODIFIED]
    assert len(modified) == 1
    assert modified[0].severity == Severity.BREAKING
    assert "integer" in modified[0].description
    assert "string" in modified[0].description
