"""Integration tests: save a baseline, run a new diff, suppress known changes."""

from __future__ import annotations

import pytest

from apidiff.baseline import load_baseline, save_baseline, suppress_baseline
from apidiff.differ import Change, ChangeType, DiffReport, Severity, diff_specs


@pytest.fixture()
def old_spec() -> dict:
    return {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.0.0"},
        "paths": {
            "/users": {"get": {"responses": {"200": {"description": "ok"}}}},
            "/items": {"get": {"responses": {"200": {"description": "ok"}}}},
        },
    }


@pytest.fixture()
def new_spec_missing_users() -> dict:
    return {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {
            "/items": {"get": {"responses": {"200": {"description": "ok"}}}},
            "/orders": {"post": {"responses": {"201": {"description": "created"}}}},
        },
    }


def test_full_baseline_roundtrip(tmp_path, old_spec, new_spec_missing_users):
    """Baseline saved from first diff suppresses those changes in second diff."""
    first_report = diff_specs(old_spec, new_spec_missing_users)
    assert len(first_report.changes) > 0

    baseline_file = tmp_path / "baseline.json"
    save_baseline(first_report, baseline_file)

    loaded = load_baseline(baseline_file)
    assert len(loaded) == len(first_report.changes)

    second_report = diff_specs(old_spec, new_spec_missing_users)
    suppressed = suppress_baseline(second_report, loaded)
    assert len(suppressed.changes) == 0


def test_new_change_surfaces_after_suppression(tmp_path, old_spec, new_spec_missing_users):
    """A change not in the baseline still appears after suppression."""
    first_report = diff_specs(old_spec, new_spec_missing_users)
    baseline_file = tmp_path / "baseline.json"
    save_baseline(first_report, baseline_file)
    loaded = load_baseline(baseline_file)

    # Introduce an additional breaking change not in the baseline
    extra_change = Change(
        change_type=ChangeType.REMOVED,
        severity=Severity.BREAKING,
        path="/extra",
        method="DELETE",
        description="Extra endpoint removed",
    )
    extended_report = DiffReport(changes=first_report.changes + [extra_change])
    suppressed = suppress_baseline(extended_report, loaded)

    assert len(suppressed.changes) == 1
    assert suppressed.changes[0].path == "/extra"
