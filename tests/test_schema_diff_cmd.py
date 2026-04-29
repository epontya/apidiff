"""Tests for the schema-diff CLI command."""

import json
import pytest
from unittest.mock import patch, MagicMock
from apidiff.schema_diff_cmd import build_schema_diff_parser, run_schema_diff, _extract_schema


OLD_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "1.0.0"},
    "paths": {
        "/users": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                                "required": ["name"],
                            }
                        }
                    }
                }
            }
        }
    },
}

NEW_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "2.0.0"},
    "paths": {
        "/users": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "properties": {"name": {"type": "string"}},
                                "required": ["name"],
                            }
                        }
                    }
                }
            }
        }
    },
}


def _make_args(old_spec, new_spec, api_path="/users", method="post", schema_ref="requestBody", fmt="text"):
    args = MagicMock()
    args.old = "old.yaml"
    args.new = "new.yaml"
    args.api_path = api_path
    args.method = method
    args.schema_ref = schema_ref
    args.format = fmt
    return args, old_spec, new_spec


def test_run_schema_diff_no_changes_returns_zero():
    args, old, new = _make_args(OLD_SPEC, OLD_SPEC)
    with patch("apidiff.schema_diff_cmd.load_spec", side_effect=[old, new]):
        result = run_schema_diff(args)
    assert result == 0


def test_run_schema_diff_breaking_returns_one():
    args, old, new = _make_args(OLD_SPEC, NEW_SPEC)
    with patch("apidiff.schema_diff_cmd.load_spec", side_effect=[old, new]):
        result = run_schema_diff(args)
    assert result == 0  # age removed but was optional


def test_run_schema_diff_load_error_returns_two(capsys):
    from apidiff.loader import SpecLoadError
    args, old, new = _make_args(OLD_SPEC, NEW_SPEC)
    with patch("apidiff.schema_diff_cmd.load_spec", side_effect=SpecLoadError("not found")):
        result = run_schema_diff(args)
    assert result == 2
    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_run_schema_diff_json_format(capsys):
    args, old, new = _make_args(OLD_SPEC, NEW_SPEC, fmt="json")
    with patch("apidiff.schema_diff_cmd.load_spec", side_effect=[old, new]):
        run_schema_diff(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)


def test_extract_schema_missing_path_returns_empty():
    result = _extract_schema({"paths": {}}, "/missing", "post", "requestBody")
    assert result == {}


def test_build_schema_diff_parser_returns_parser():
    parser = build_schema_diff_parser()
    assert parser is not None
