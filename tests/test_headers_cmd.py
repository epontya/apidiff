"""Tests for apidiff.headers_cmd."""

import json
import pytest
from unittest.mock import patch
from apidiff.headers_cmd import build_headers_parser, run_headers


@pytest.fixture
def base_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "headers": {
                                "X-Rate-Limit": {"required": True, "schema": {"type": "integer"}}
                            },
                        }
                    }
                }
            }
        },
    }
    f = tmp_path / "base.json"
    f.write_text(json.dumps(spec))
    return str(f)


@pytest.fixture
def breaking_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "2.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "headers": {},
                        }
                    }
                }
            }
        },
    }
    f = tmp_path / "breaking.json"
    f.write_text(json.dumps(spec))
    return str(f)


@pytest.fixture
def safe_file(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "API", "version": "1.1.0"},
        "paths": {
            "/items": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "headers": {
                                "X-Rate-Limit": {"required": True, "schema": {"type": "integer"}},
                                "X-New": {"schema": {"type": "string"}},
                            },
                        }
                    }
                }
            }
        },
    }
    f = tmp_path / "safe.json"
    f.write_text(json.dumps(spec))
    return str(f)


def _make_args(old, new, fmt="text", fail_on_breaking=False):
    parser = build_headers_parser()
    return parser.parse_args(
        [old, new, "--format", fmt]
        + (["--fail-on-breaking"] if fail_on_breaking else [])
    )


def test_no_breaking_returns_zero(base_file, safe_file):
    args = _make_args(base_file, safe_file)
    assert run_headers(args) == 0


def test_breaking_without_flag_returns_zero(base_file, breaking_file):
    args = _make_args(base_file, breaking_file)
    assert run_headers(args) == 0


def test_breaking_with_flag_returns_one(base_file, breaking_file):
    args = _make_args(base_file, breaking_file, fail_on_breaking=True)
    assert run_headers(args) == 1


def test_missing_file_returns_two(tmp_path, base_file):
    args = _make_args(base_file, str(tmp_path / "missing.json"))
    assert run_headers(args) == 2


def test_json_format_produces_valid_json(base_file, breaking_file, capsys):
    args = _make_args(base_file, breaking_file, fmt="json")
    run_headers(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "changes" in data or isinstance(data, dict)
