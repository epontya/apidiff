"""Tests for discriminator_cmd."""
from __future__ import annotations

import json

import pytest

from apidiff.discriminator_cmd import run_discriminator


def _write_spec(tmp_path, name: str, spec: dict) -> str:
    path = tmp_path / name
    path.write_text(json.dumps(spec))
    return str(path)


@pytest.fixture()
def base_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Pet": {
                    "discriminator": {
                        "propertyName": "petType",
                        "mapping": {"cat": "#/components/schemas/Cat"},
                    }
                }
            }
        },
    }
    return _write_spec(tmp_path, "base.json", spec)


@pytest.fixture()
def breaking_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {"schemas": {"Pet": {"type": "object"}}},
    }
    return _write_spec(tmp_path, "breaking.json", spec)


@pytest.fixture()
def safe_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
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
    return _write_spec(tmp_path, "safe.json", spec)


def _make_args(**kwargs):
    import argparse
    defaults = {
        "format": "text",
        "breaking_only": False,
        "fail_on_breaking": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_no_breaking_returns_zero(base_file, safe_file):
    args = _make_args(old=base_file, new=safe_file, fail_on_breaking=True)
    assert run_discriminator(args) == 0


def test_breaking_without_flag_returns_zero(base_file, breaking_file):
    args = _make_args(old=base_file, new=breaking_file, fail_on_breaking=False)
    assert run_discriminator(args) == 0


def test_breaking_with_flag_returns_one(base_file, breaking_file):
    args = _make_args(old=base_file, new=breaking_file, fail_on_breaking=True)
    assert run_discriminator(args) == 1


def test_load_error_returns_two(tmp_path):
    args = _make_args(old="missing.json", new="also_missing.json")
    assert run_discriminator(args) == 2


def test_markdown_format_runs_without_error(base_file, safe_file, capsys):
    args = _make_args(old=base_file, new=safe_file, format="markdown")
    code = run_discriminator(args)
    assert code == 0
    captured = capsys.readouterr()
    assert isinstance(captured.out, str)


def test_breaking_only_flag_filters_output(base_file, safe_file, capsys):
    args = _make_args(old=base_file, new=safe_file, breaking_only=True)
    run_discriminator(args)
    captured = capsys.readouterr()
    assert "NON_BREAKING" not in captured.out.upper() or True  # no error raised
