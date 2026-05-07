"""Tests for constraints_cmd."""
import json
import pytest
from unittest.mock import patch
from pathlib import Path
import yaml

from apidiff.constraints_cmd import run_constraints


def _write_spec(tmp_path: Path, name: str, spec: dict) -> str:
    p = tmp_path / name
    p.write_text(yaml.dump(spec))
    return str(p)


@pytest.fixture
def base_file(tmp_path):
    spec = {
        "info": {"version": "1.0.0"},
        "components": {
            "schemas": {
                "Item": {
                    "properties": {
                        "name": {"type": "string", "minLength": 1, "maxLength": 50},
                    }
                }
            }
        },
    }
    return _write_spec(tmp_path, "base.yaml", spec)


@pytest.fixture
def breaking_file(tmp_path):
    spec = {
        "info": {"version": "2.0.0"},
        "components": {
            "schemas": {
                "Item": {
                    "properties": {
                        "name": {"type": "string", "minLength": 10, "maxLength": 50},
                    }
                }
            }
        },
    }
    return _write_spec(tmp_path, "breaking.yaml", spec)


@pytest.fixture
def safe_file(tmp_path):
    spec = {
        "info": {"version": "1.1.0"},
        "components": {
            "schemas": {
                "Item": {
                    "properties": {
                        "name": {"type": "string", "minLength": 1, "maxLength": 50},
                    }
                }
            }
        },
    }
    return _write_spec(tmp_path, "safe.yaml", spec)


def _make_args(old, new, breaking_only=False, fail_on_breaking=False, fmt="text"):
    import argparse
    return argparse.Namespace(
        old=old, new=new,
        breaking_only=breaking_only,
        fail_on_breaking=fail_on_breaking,
        format=fmt,
    )


def test_no_breaking_returns_zero(base_file, safe_file):
    args = _make_args(base_file, safe_file, fail_on_breaking=True)
    assert run_constraints(args) == 0


def test_breaking_returns_one_with_flag(base_file, breaking_file):
    args = _make_args(base_file, breaking_file, fail_on_breaking=True)
    assert run_constraints(args) == 1


def test_breaking_without_flag_returns_zero(base_file, breaking_file):
    args = _make_args(base_file, breaking_file, fail_on_breaking=False)
    assert run_constraints(args) == 0


def test_missing_file_returns_two(base_file):
    args = _make_args(base_file, "nonexistent.yaml")
    assert run_constraints(args) == 2


def test_breaking_only_flag_filters_output(base_file, breaking_file, capsys):
    args = _make_args(base_file, breaking_file, breaking_only=True)
    run_constraints(args)
    captured = capsys.readouterr()
    assert "minLength" in captured.out
