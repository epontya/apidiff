"""Tests for writeonly_cmd."""
import json
import textwrap
from pathlib import Path

import pytest

from apidiff.writeonly_cmd import run_writeonly, build_writeonly_parser


def _write_spec(tmp_path: Path, name: str, spec: dict) -> str:
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
                "User": {
                    "properties": {"password": {"type": "string", "writeOnly": True}}
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
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "password": {"type": "string", "writeOnly": True},
                        "name": {"type": "string", "writeOnly": True},
                    }
                }
            }
        },
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
                "User": {
                    "properties": {"password": {"type": "string"}}
                }
            }
        },
    }
    return _write_spec(tmp_path, "safe.json", spec)


def _make_args(old, new, fmt="text", fail_on_breaking=False):
    parser = build_writeonly_parser()
    argv = [old, new, "--format", fmt]
    if fail_on_breaking:
        argv.append("--fail-on-breaking")
    return parser.parse_args(argv)


def test_no_breaking_returns_zero(base_file):
    args = _make_args(base_file, base_file, fail_on_breaking=True)
    assert run_writeonly(args) == 0


def test_breaking_without_flag_returns_zero(base_file, breaking_file):
    args = _make_args(base_file, breaking_file, fail_on_breaking=False)
    assert run_writeonly(args) == 0


def test_breaking_with_flag_returns_one(base_file, breaking_file):
    args = _make_args(base_file, breaking_file, fail_on_breaking=True)
    assert run_writeonly(args) == 1


def test_non_breaking_removal_returns_zero_with_flag(base_file, safe_file):
    args = _make_args(base_file, safe_file, fail_on_breaking=True)
    assert run_writeonly(args) == 0


def test_missing_file_returns_two(tmp_path, base_file):
    args = _make_args(base_file, str(tmp_path / "missing.json"))
    assert run_writeonly(args) == 2
