"""Tests for apidiff.impact_cmd CLI entry point."""

import json
import pytest

from apidiff.impact_cmd import run_impact, build_impact_parser


def _make_args(old, new, fmt="text", fail_on_impact=False):
    parser = build_impact_parser()
    argv = [old, new, "--format", fmt]
    if fail_on_impact:
        argv.append("--fail-on-impact")
    return parser.parse_args(argv)


@pytest.fixture()
def base_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.0"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "OK"}}}
            }
        },
    }
    import json as _json
    p = tmp_path / "base.json"
    p.write_text(_json.dumps(spec))
    return str(p)


@pytest.fixture()
def breaking_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "2.0"},
        "paths": {},
    }
    import json as _json
    p = tmp_path / "breaking.json"
    p.write_text(_json.dumps(spec))
    return str(p)


@pytest.fixture()
def safe_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.1"},
        "paths": {
            "/users": {
                "get": {"responses": {"200": {"description": "OK"}}},
                "post": {"responses": {"201": {"description": "Created"}}},
            }
        },
    }
    import json as _json
    p = tmp_path / "safe.json"
    p.write_text(_json.dumps(spec))
    return str(p)


def test_no_impact_returns_zero(base_file, safe_file):
    args = _make_args(base_file, safe_file)
    assert run_impact(args) == 0


def test_breaking_change_returns_zero_without_flag(base_file, breaking_file):
    args = _make_args(base_file, breaking_file)
    assert run_impact(args) == 0


def test_breaking_change_returns_one_with_flag(base_file, breaking_file):
    args = _make_args(base_file, breaking_file, fail_on_impact=True)
    assert run_impact(args) == 1


def test_missing_file_returns_two(base_file):
    args = _make_args(base_file, "nonexistent.json")
    assert run_impact(args) == 2


def test_json_format_is_valid_json(base_file, breaking_file, capsys):
    args = _make_args(base_file, breaking_file, fmt="json")
    run_impact(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "impacted_areas" in data


def test_text_format_contains_path(base_file, breaking_file, capsys):
    args = _make_args(base_file, breaking_file, fmt="text")
    run_impact(args)
    captured = capsys.readouterr()
    assert "/users" in captured.out
