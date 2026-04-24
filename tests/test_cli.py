"""Tests for the apidiff CLI module."""

import json
import os
import pytest

from apidiff.cli import main, build_parser


BASE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {"responses": {"200": {"description": "OK"}}}
        }
    },
}

REVISION_SPEC_BREAKING = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "2.0.0"},
    "paths": {},
}

REVISION_SPEC_SAFE = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "1.1.0"},
    "paths": {
        "/users": {
            "get": {"responses": {"200": {"description": "OK"}}}
        },
        "/items": {
            "get": {"responses": {"200": {"description": "OK"}}}
        },
    },
}


@pytest.fixture
def base_file(tmp_path):
    f = tmp_path / "base.json"
    f.write_text(json.dumps(BASE_SPEC))
    return str(f)


@pytest.fixture
def breaking_file(tmp_path):
    f = tmp_path / "revision_breaking.json"
    f.write_text(json.dumps(REVISION_SPEC_BREAKING))
    return str(f)


@pytest.fixture
def safe_file(tmp_path):
    f = tmp_path / "revision_safe.json"
    f.write_text(json.dumps(REVISION_SPEC_SAFE))
    return str(f)


def test_main_returns_zero_on_no_breaking(base_file, safe_file):
    result = main([base_file, safe_file])
    assert result == 0


def test_main_returns_zero_without_flag_even_if_breaking(base_file, breaking_file):
    result = main([base_file, breaking_file])
    assert result == 0


def test_main_returns_one_with_fail_on_breaking(base_file, breaking_file):
    result = main([base_file, breaking_file, "--fail-on-breaking"])
    assert result == 1


def test_main_returns_two_on_missing_file(tmp_path):
    result = main(["nonexistent_base.json", "nonexistent_rev.json"])
    assert result == 2


def test_main_json_format_output(base_file, safe_file, capsys):
    main([base_file, safe_file, "--format", "json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "changes" in parsed


def test_main_writes_output_file(base_file, safe_file, tmp_path):
    out_file = str(tmp_path / "report.txt")
    main([base_file, safe_file, "--output", out_file])
    assert os.path.exists(out_file)
    assert os.path.getsize(out_file) > 0


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["base.yaml", "rev.yaml"])
    assert args.format == "text"
    assert args.output is None
    assert args.fail_on_breaking is False
