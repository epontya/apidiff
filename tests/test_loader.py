"""Tests for apidiff.loader module."""

import json
import os
import textwrap

import pytest

from apidiff.loader import SpecLoadError, load_spec


MINIMAL_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {},
}


@pytest.fixture()
def json_spec_file(tmp_path):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(MINIMAL_SPEC), encoding="utf-8")
    return str(spec_path)


@pytest.fixture()
def yaml_spec_file(tmp_path):
    content = textwrap.dedent("""\
        openapi: "3.0.0"
        info:
          title: Test API
          version: "1.0.0"
        paths: {}
    """)
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(content, encoding="utf-8")
    return str(spec_path)


def test_load_json_spec(json_spec_file):
    spec = load_spec(json_spec_file)
    assert spec["openapi"] == "3.0.0"
    assert "paths" in spec


def test_load_yaml_spec(yaml_spec_file):
    pytest.importorskip("yaml")
    spec = load_spec(yaml_spec_file)
    assert spec["openapi"] == "3.0.0"
    assert spec["info"]["title"] == "Test API"


def test_file_not_found():
    with pytest.raises(SpecLoadError, match="File not found"):
        load_spec("/nonexistent/path/spec.json")


def test_unsupported_extension(tmp_path):
    bad_file = tmp_path / "spec.txt"
    bad_file.write_text("{}", encoding="utf-8")
    with pytest.raises(SpecLoadError, match="Unsupported file extension"):
        load_spec(str(bad_file))


def test_invalid_json(tmp_path):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{ not valid json ", encoding="utf-8")
    with pytest.raises(SpecLoadError, match="JSON parse error"):
        load_spec(str(bad_json))


def test_missing_openapi_field(tmp_path):
    spec = {"info": {"title": "X", "version": "1"}, "paths": {}}
    f = tmp_path / "spec.json"
    f.write_text(json.dumps(spec), encoding="utf-8")
    with pytest.raises(SpecLoadError, match="openapi"):
        load_spec(str(f))


def test_missing_paths_field(tmp_path):
    spec = {"openapi": "3.0.0", "info": {"title": "X", "version": "1"}}
    f = tmp_path / "spec.json"
    f.write_text(json.dumps(spec), encoding="utf-8")
    with pytest.raises(SpecLoadError, match="paths"):
        load_spec(str(f))


def test_spec_not_a_dict(tmp_path):
    f = tmp_path / "spec.json"
    f.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(SpecLoadError, match="must be a JSON/YAML object"):
        load_spec(str(f))
