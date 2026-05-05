"""Tests for apidiff.webhooks_cmd."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from apidiff.webhooks_cmd import run_webhooks, build_webhooks_parser


def _write_spec(tmp_path: Path, name: str, webhooks: dict) -> Path:
    import yaml

    spec = {
        "openapi": "3.1.0",
        "info": {"title": "T", "version": "1.0.0"},
        "paths": {},
        "webhooks": webhooks,
    }
    p = tmp_path / name
    p.write_text(yaml.dump(spec))
    return p


@pytest.fixture()
def base_file(tmp_path):
    return _write_spec(tmp_path, "base.yaml", {
        "orderCreated": {"post": {"responses": {"200": {"description": "OK"}}}}
    })


@pytest.fixture()
def breaking_file(tmp_path):
    return _write_spec(tmp_path, "breaking.yaml", {})


@pytest.fixture()
def safe_file(tmp_path):
    return _write_spec(tmp_path, "safe.yaml", {
        "orderCreated": {"post": {"responses": {"200": {"description": "OK"}}}},
        "orderUpdated": {"put": {"responses": {"200": {"description": "OK"}}}},
    })


def _make_args(old, new, breaking_only=False, fail_on_breaking=False, fmt="text"):
    parser = build_webhooks_parser()
    return parser.parse_args([
        str(old), str(new),
        *([ "--breaking-only"] if breaking_only else []),
        *([ "--fail-on-breaking"] if fail_on_breaking else []),
        "--format", fmt,
    ])


def test_no_breaking_returns_zero(base_file, safe_file):
    args = _make_args(base_file, safe_file, fail_on_breaking=True)
    assert run_webhooks(args) == 0


def test_breaking_without_flag_returns_zero(base_file, breaking_file):
    args = _make_args(base_file, breaking_file)
    assert run_webhooks(args) == 0


def test_breaking_with_flag_returns_one(base_file, breaking_file):
    args = _make_args(base_file, breaking_file, fail_on_breaking=True)
    assert run_webhooks(args) == 1


def test_load_error_returns_two(tmp_path, base_file):
    missing = tmp_path / "missing.yaml"
    args = _make_args(base_file, missing)
    assert run_webhooks(args) == 2


def test_breaking_only_flag_filters_output(base_file, safe_file, capsys):
    args = _make_args(base_file, safe_file, breaking_only=True)
    run_webhooks(args)
    captured = capsys.readouterr()
    assert "orderUpdated" not in captured.out or "BREAKING" not in captured.out
