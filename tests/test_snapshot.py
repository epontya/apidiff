"""Tests for apidiff.snapshot module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apidiff.snapshot import SnapshotError, load_snapshot, save_snapshot, snapshot_exists


@pytest.fixture()
def minimal_spec_file(tmp_path) -> Path:
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {"/ping": {"get": {"responses": {"200": {"description": "ok"}}}}},
    }
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    return p


def test_save_snapshot_creates_file(tmp_path, minimal_spec_file):
    dest = tmp_path / "snap.json"
    save_snapshot(minimal_spec_file, dest)
    assert dest.exists()


def test_save_snapshot_content_matches_spec(tmp_path, minimal_spec_file):
    dest = tmp_path / "snap.json"
    save_snapshot(minimal_spec_file, dest)
    data = json.loads(dest.read_text())
    assert data["openapi"] == "3.0.0"
    assert "/ping" in data["paths"]


def test_load_snapshot_returns_dict(tmp_path, minimal_spec_file):
    dest = tmp_path / "snap.json"
    save_snapshot(minimal_spec_file, dest)
    result = load_snapshot(dest)
    assert isinstance(result, dict)
    assert result["info"]["title"] == "Test"


def test_load_snapshot_missing_raises(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot(tmp_path / "ghost.json")


def test_load_snapshot_corrupt_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{{invalid", encoding="utf-8")
    with pytest.raises(SnapshotError):
        load_snapshot(bad)


def test_snapshot_exists_true(tmp_path, minimal_spec_file):
    dest = tmp_path / "snap.json"
    save_snapshot(minimal_spec_file, dest)
    assert snapshot_exists(dest) is True


def test_snapshot_exists_false(tmp_path):
    assert snapshot_exists(tmp_path / "nope.json") is False


def test_save_snapshot_bad_dest_raises(minimal_spec_file):
    with pytest.raises(SnapshotError):
        save_snapshot(minimal_spec_file, "/no_such_dir/snap.json")
