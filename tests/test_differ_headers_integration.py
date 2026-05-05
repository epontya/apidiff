"""Integration tests: diff_headers combined with filters and summary."""

import pytest
from apidiff.differ import ChangeType, Severity
from apidiff.differ_headers import diff_headers
from apidiff.filters import filter_breaking_only, filter_non_breaking_only
from apidiff.summary import summarize


@pytest.fixture
def old_spec():
    return {
        "info": {"version": "1.0.0"},
        "paths": {
            "/orders": {
                "post": {
                    "responses": {
                        "201": {
                            "headers": {
                                "Location": {"required": True, "schema": {"type": "string"}},
                                "X-Trace-Id": {"required": False, "schema": {"type": "string"}},
                            }
                        }
                    }
                }
            }
        },
    }


@pytest.fixture
def new_spec_breaking():
    """Removes required Location header and changes X-Trace-Id type."""
    return {
        "info": {"version": "2.0.0"},
        "paths": {
            "/orders": {
                "post": {
                    "responses": {
                        "201": {
                            "headers": {
                                "X-Trace-Id": {"required": False, "schema": {"type": "integer"}},
                            }
                        }
                    }
                }
            }
        },
    }


def test_breaking_only_filter_isolates_breaking_changes(old_spec, new_spec_breaking):
    report = diff_headers(old_spec, new_spec_breaking)
    breaking_report = filter_breaking_only(report)
    assert all(c.severity == Severity.BREAKING for c in breaking_report.changes)
    assert len(breaking_report.changes) >= 1


def test_non_breaking_filter_returns_empty_for_all_breaking(old_spec, new_spec_breaking):
    report = diff_headers(old_spec, new_spec_breaking)
    non_breaking = filter_non_breaking_only(report)
    assert all(c.severity == Severity.NON_BREAKING for c in non_breaking.changes)


def test_summary_counts_match_changes(old_spec, new_spec_breaking):
    report = diff_headers(old_spec, new_spec_breaking)
    summary = summarize(report)
    assert summary.total == len(report.changes)
    breaking_count = sum(1 for c in report.changes if c.severity == Severity.BREAKING)
    assert summary.breaking == breaking_count


def test_added_header_appears_as_non_breaking(old_spec):
    new_spec = {
        "info": {"version": "1.1.0"},
        "paths": {
            "/orders": {
                "post": {
                    "responses": {
                        "201": {
                            "headers": {
                                "Location": {"required": True, "schema": {"type": "string"}},
                                "X-Trace-Id": {"required": False, "schema": {"type": "string"}},
                                "X-Extra": {"schema": {"type": "string"}},
                            }
                        }
                    }
                }
            }
        },
    }
    report = diff_headers(old_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].severity == Severity.NON_BREAKING
