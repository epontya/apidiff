"""Tests for differ_extensions_discriminator."""
from __future__ import annotations

import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.differ_extensions_discriminator import diff_discriminator


@pytest.fixture()
def base_spec() -> dict:
    return {
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "Pet": {
                    "discriminator": {
                        "propertyName": "petType",
                        "mapping": {
                            "cat": "#/components/schemas/Cat",
                            "dog": "#/components/schemas/Dog",
                        },
                    }
                }
            }
        },
    }


def _new(base_spec, schema_override):
    import copy
    spec = copy.deepcopy(base_spec)
    spec["info"]["version"] = "2.0.0"
    spec["components"]["schemas"]["Pet"] = schema_override
    return spec


def test_no_changes_returns_empty_report(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["info"]["version"] = "2.0.0"
    report = diff_discriminator(base_spec, new_spec)
    assert report.changes == []


def test_versions_are_set(base_spec):
    import copy
    new_spec = copy.deepcopy(base_spec)
    new_spec["info"]["version"] = "2.0.0"
    report = diff_discriminator(base_spec, new_spec)
    assert report.old_version == "1.0.0"
    assert report.new_version == "2.0.0"


def test_removed_discriminator_is_breaking(base_spec):
    new_spec = _new(base_spec, {"type": "object"})
    report = diff_discriminator(base_spec, new_spec)
    assert len(report.changes) == 1
    assert report.changes[0].severity == Severity.BREAKING
    assert report.changes[0].change_type == ChangeType.REMOVED


def test_added_discriminator_is_non_breaking(base_spec):
    import copy
    old_spec = copy.deepcopy(base_spec)
    old_spec["components"]["schemas"]["Pet"] = {"type": "object"}
    new_spec = copy.deepcopy(base_spec)
    new_spec["info"]["version"] = "2.0.0"
    report = diff_discriminator(old_spec, new_spec)
    assert len(report.changes) == 1
    assert report.changes[0].severity == Severity.NON_BREAKING
    assert report.changes[0].change_type == ChangeType.ADDED


def test_property_name_change_is_breaking(base_spec):
    new_spec = _new(base_spec, {
        "discriminator": {
            "propertyName": "kind",
            "mapping": {
                "cat": "#/components/schemas/Cat",
                "dog": "#/components/schemas/Dog",
            },
        }
    })
    report = diff_discriminator(base_spec, new_spec)
    assert any(c.severity == Severity.BREAKING for c in report.changes)
    assert any("propertyName" in c.path for c in report.changes)


def test_removed_mapping_key_is_breaking(base_spec):
    new_spec = _new(base_spec, {
        "discriminator": {
            "propertyName": "petType",
            "mapping": {"cat": "#/components/schemas/Cat"},
        }
    })
    report = diff_discriminator(base_spec, new_spec)
    breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
    assert any("dog" in c.path for c in breaking)


def test_added_mapping_key_is_non_breaking(base_spec):
    new_spec = _new(base_spec, {
        "discriminator": {
            "propertyName": "petType",
            "mapping": {
                "cat": "#/components/schemas/Cat",
                "dog": "#/components/schemas/Dog",
                "fish": "#/components/schemas/Fish",
            },
        }
    })
    report = diff_discriminator(base_spec, new_spec)
    added = [c for c in report.changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert "fish" in added[0].path
    assert added[0].severity == Severity.NON_BREAKING


def test_changed_mapping_value_is_breaking(base_spec):
    new_spec = _new(base_spec, {
        "discriminator": {
            "propertyName": "petType",
            "mapping": {
                "cat": "#/components/schemas/Feline",
                "dog": "#/components/schemas/Dog",
            },
        }
    })
    report = diff_discriminator(base_spec, new_spec)
    modified = [c for c in report.changes if c.change_type == ChangeType.MODIFIED]
    assert len(modified) == 1
    assert modified[0].severity == Severity.BREAKING
