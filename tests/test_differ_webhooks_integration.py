"""Integration tests for webhook diffing with filters and summary."""
import pytest
from apidiff.differ_webhooks import diff_webhooks
from apidiff.filters import filter_breaking_only, filter_non_breaking_only
from apidiff.summary import summarize


@pytest.fixture()
def old_spec():
    return {
        "openapi": "3.1.0",
        "info": {"title": "API", "version": "1.0.0"},
        "paths": {},
        "webhooks": {
            "orderCreated": {
                "post": {"responses": {"200": {"description": "OK"}}},
            },
            "orderCancelled": {
                "delete": {"responses": {"200": {"description": "OK"}}},
            },
        },
    }


@pytest.fixture()
def new_spec_breaking():
    return {
        "openapi": "3.1.0",
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "webhooks": {
            "orderCreated": {
                "post": {"responses": {"200": {"description": "OK"}}},
                "get": {"responses": {"200": {"description": "OK"}}},
            },
            # orderCancelled removed — breaking
        },
    }


def test_breaking_filter_isolates_breaking_changes(old_spec, new_spec_breaking):
    report = diff_webhooks(old_spec, new_spec_breaking)
    breaking = filter_breaking_only(report)
    assert all(c.severity.value == "breaking" for c in breaking.changes)
    assert len(breaking.changes) >= 1


def test_non_breaking_filter_returns_added_only(old_spec, new_spec_breaking):
    report = diff_webhooks(old_spec, new_spec_breaking)
    non_breaking = filter_non_breaking_only(report)
    assert all(c.severity.value == "non_breaking" for c in non_breaking.changes)


def test_summary_counts_match_changes(old_spec, new_spec_breaking):
    report = diff_webhooks(old_spec, new_spec_breaking)
    summary = summarize(report)
    total = summary.breaking_count + summary.non_breaking_count
    assert total == summary.total_count
    assert summary.total_count == len(report.changes)


def test_versions_preserved_through_filter(old_spec, new_spec_breaking):
    report = diff_webhooks(old_spec, new_spec_breaking)
    breaking = filter_breaking_only(report)
    assert breaking.old_version == "1.0.0"
    assert breaking.new_version == "2.0.0"
