"""Integration tests for discriminator diffing with filters and summary."""
from __future__ import annotations

import pytest

from apidiff.differ import Severity
from apidiff.differ_extensions_discriminator import diff_discriminator
from apidiff.filters import filter_breaking_only, filter_non_breaking_only
from apidiff.summary import summarize


@pytest.fixture()
def old_spec() -> dict:
    return {
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "Shape": {
                    "discriminator": {
                        "propertyName": "shapeType",
                        "mapping": {
                            "circle": "#/components/schemas/Circle",
                            "square": "#/components/schemas/Square",
                        },
                    }
                }
            }
        },
    }


@pytest.fixture()
def new_spec_breaking() -> dict:
    return {
        "info": {"version": "2.0.0"},
        "components": {
            "schemas": {
                "Shape": {
                    "discriminator": {
                        "propertyName": "kind",  # changed — breaking
                        "mapping": {
                            # 'square' removed — breaking
                            "circle": "#/components/schemas/Circle",
                            "triangle": "#/components/schemas/Triangle",  # added — non-breaking
                        },
                    }
                }
            }
        },
    }


def test_breaking_filter_isolates_breaking_changes(old_spec, new_spec_breaking):
    report = diff_discriminator(old_spec, new_spec_breaking)
    breaking = filter_breaking_only(report)
    assert all(c.severity == Severity.BREAKING for c in breaking.changes)
    assert len(breaking.changes) >= 1


def test_non_breaking_filter_returns_added_only(old_spec, new_spec_breaking):
    report = diff_discriminator(old_spec, new_spec_breaking)
    non_breaking = filter_non_breaking_only(report)
    assert all(c.severity == Severity.NON_BREAKING for c in non_breaking.changes)


def test_summary_counts_match_changes(old_spec, new_spec_breaking):
    report = diff_discriminator(old_spec, new_spec_breaking)
    summary = summarize(report)
    assert summary.total == len(report.changes)
    breaking_count = sum(1 for c in report.changes if c.severity == Severity.BREAKING)
    assert summary.breaking == breaking_count


def test_versions_preserved_through_filter(old_spec, new_spec_breaking):
    report = diff_discriminator(old_spec, new_spec_breaking)
    filtered = filter_breaking_only(report)
    assert filtered.old_version == "1.0.0"
    assert filtered.new_version == "2.0.0"
