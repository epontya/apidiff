"""Integration tests for apidiff.tracer_cmd."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from apidiff.tracer_cmd import build_tracer_parser, run_tracer


def _write_spec(tmp_path: Path, name: str, content: dict) -> Path:
    import yaml  # type: ignore

    p = tmp_path / name
    p.write_text(yaml.dump(content))
    return p


_BASE = {
    "openapi": "3.0.0",
    "info": {"title": "API", "version": "1.0.0"},
    "paths": {
        "/users": {"get": {"responses": {"200": {"description": "ok"}}}},
        "/orders": {"post": {"responses": {"201": {"description": "created"}}}},
    },
}

_BREAKING = {
    "openapi": "3.0.0",
    "info": {"title": "API", "version": "2.0.0"},
    "paths": {
        "/orders": {"post": {"responses": {"201": {"description": "created"}}}},
    },
}


@pytest.fixture()
def base_file(tmp_path: Path) -> Path:
    return _write_spec(tmp_path, "base.yaml", _BASE)


@pytest.fixture()
def breaking_file(tmp_path: Path) -> Path:
    return _write_spec(tmp_path, "breaking.yaml", _BREAKING)


def _make_args(old, new, pattern, operation=None, fmt="text", fail_on_breaking=False):
    parser = build_tracer_parser()
    argv = [str(old), str(new), pattern, "--format", fmt]
    if operation:
        argv += ["--operation", operation]
    if fail_on_breaking:
        argv.append("--fail-on-breaking")
    return parser.parse_args(argv)


def test_no_match_returns_zero(base_file, breaking_file):
    args = _make_args(base_file, breaking_file, "/orders*")
    assert run_tracer(args) == 0


def test_breaking_match_without_flag_returns_zero(base_file, breaking_file):
    args = _make_args(base_file, breaking_file, "/users*")
    assert run_tracer(args) == 0


def test_breaking_match_with_flag_returns_one(base_file, breaking_file):
    args = _make_args(base_file, breaking_file, "/users*", fail_on_breaking=True)
    assert run_tracer(args) == 1


def test_json_format_is_valid_json(base_file, breaking_file, capsys):
    args = _make_args(base_file, breaking_file, "/users*", fmt="json")
    run_tracer(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "matched" in data
    assert data["pattern"] == "/users*"


def test_load_error_returns_two(tmp_path, breaking_file):
    missing = tmp_path / "missing.yaml"
    args = _make_args(missing, breaking_file, "/users")
    assert run_tracer(args) == 2


def test_text_output_contains_breaking_label(base_file, breaking_file, capsys):
    args = _make_args(base_file, breaking_file, "/users*")
    run_tracer(args)
    captured = capsys.readouterr()
    assert "BREAKING" in captured.out
