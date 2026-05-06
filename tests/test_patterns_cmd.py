"""Tests for apidiff.patterns_cmd."""

from __future__ import annotations

import json
import argparse

import pytest

from apidiff.patterns_cmd import build_patterns_parser, run_patterns


def _write_spec(tmp_path, name: str, spec: dict) -> str:
    import yaml

    path = tmp_path / name
    path.write_text(yaml.dump(spec))
    return str(path)


@pytest.fixture()
def base_file(tmp_path):
    return _write_spec(tmp_path, "base.yaml", {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string", "pattern": "^[\\w]+@[\\w]+\\.com$"},
                    }
                }
            }
        },
    })


@pytest.fixture()
def breaking_file(tmp_path):
    return _write_spec(tmp_path, "breaking.yaml", {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string", "pattern": "^[\\w]+@[\\w]+\\.[a-z]{2,4}$"},
                    }
                }
            }
        },
    })


@pytest.fixture()
def safe_file(tmp_path):
    return _write_spec(tmp_path, "safe.yaml", {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "User": {
                    "properties": {
                        "email": {"type": "string", "pattern": "^[\\w]+@[\\w]+\\.com$"},
                    }
                }
            }
        },
    })


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"fmt": "text", "breaking_only": False, "fail_on_breaking": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_no_breaking_returns_zero(base_file, safe_file):
    args = _make_args(old=base_file, new=safe_file)
    assert run_patterns(args) == 0


def test_breaking_without_flag_returns_zero(base_file, breaking_file):
    args = _make_args(old=base_file, new=breaking_file)
    assert run_patterns(args) == 0


def test_breaking_with_flag_returns_one(base_file, breaking_file):
    args = _make_args(old=base_file, new=breaking_file, fail_on_breaking=True)
    assert run_patterns(args) == 1


def test_missing_file_returns_two(safe_file):
    args = _make_args(old="nonexistent.yaml", new=safe_file)
    assert run_patterns(args) == 2


def test_build_patterns_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    build_patterns_parser(subparsers)
    parsed = parser.parse_args(["patterns", "old.yaml", "new.yaml"])
    assert parsed.old == "old.yaml"
    assert parsed.new == "new.yaml"
