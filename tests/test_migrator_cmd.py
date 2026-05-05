"""Integration tests for apidiff.migrator_cmd."""

import json
import types
import pytest

from apidiff.migrator_cmd import build_migrator_parser, run_migrator


@pytest.fixture()
def base_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"summary": "List users", "responses": {"200": {"description": "OK"}}}
            }
        },
    }
    p = tmp_path / "base.json"
    p.write_text(json.dumps(spec))
    return str(p)


@pytest.fixture()
def breaking_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "2.0.0"},
        "paths": {},
    }
    p = tmp_path / "breaking.json"
    p.write_text(json.dumps(spec))
    return str(p)


@pytest.fixture()
def safe_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.1.0"},
        "paths": {
            "/users": {
                "get": {"summary": "List users", "responses": {"200": {"description": "OK"}}}
            },
            "/items": {
                "get": {"summary": "List items", "responses": {"200": {"description": "OK"}}}
            },
        },
    }
    p = tmp_path / "safe.json"
    p.write_text(json.dumps(spec))
    return str(p)


def _make_args(**kwargs):
    defaults = {"format": "text", "output": None}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def test_no_breaking_returns_zero(base_file, safe_file):
    args = _make_args(old_spec=base_file, new_spec=safe_file)
    assert run_migrator(args) == 0


def test_breaking_returns_one(base_file, breaking_file):
    args = _make_args(old_spec=base_file, new_spec=breaking_file)
    assert run_migrator(args) == 1


def test_missing_file_returns_two(base_file):
    args = _make_args(old_spec=base_file, new_spec="/nonexistent/spec.json")
    assert run_migrator(args) == 2


def test_json_format_is_valid_json(base_file, breaking_file, capsys):
    args = _make_args(old_spec=base_file, new_spec=breaking_file, format="json")
    run_migrator(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "hints" in data
    assert isinstance(data["hints"], list)


def test_output_written_to_file(base_file, breaking_file, tmp_path):
    out = tmp_path / "plan.txt"
    args = _make_args(old_spec=base_file, new_spec=breaking_file, output=str(out))
    run_migrator(args)
    assert out.exists()
    assert len(out.read_text()) > 0


def test_parser_has_format_option():
    parser = build_migrator_parser()
    args = parser.parse_args(["old.json", "new.json", "--format", "json"])
    assert args.format == "json"
