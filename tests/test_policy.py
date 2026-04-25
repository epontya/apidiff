"""Tests for apidiff.policy module."""

import json
import pytest

from apidiff.differ import ChangeType, Severity
from apidiff.policy import PolicyLoadError, load_policy


VALID_POLICY_YAML = """
rules:
  - name: no-breaking
    description: No breaking changes.
    max_breaking_changes: 0
  - name: no-removals
    description: No removed paths.
    forbidden_change_types:
      - removed
"""

VALID_POLICY_JSON = json.dumps({
    "rules": [
        {
            "name": "severity-gate",
            "description": "Block error-level changes.",
            "severity_threshold": "error",
        }
    ]
})


@pytest.fixture()
def yaml_policy_file(tmp_path):
    p = tmp_path / "policy.yaml"
    p.write_text(VALID_POLICY_YAML)
    return str(p)


@pytest.fixture()
def json_policy_file(tmp_path):
    p = tmp_path / "policy.json"
    p.write_text(VALID_POLICY_JSON)
    return str(p)


def test_load_yaml_policy_returns_rules(yaml_policy_file):
    rules = load_policy(yaml_policy_file)
    assert len(rules) == 2
    assert rules[0].name == "no-breaking"
    assert rules[0].max_breaking_changes == 0


def test_load_yaml_forbidden_change_types(yaml_policy_file):
    rules = load_policy(yaml_policy_file)
    assert ChangeType.REMOVED in rules[1].forbidden_change_types


def test_load_json_policy_returns_rules(json_policy_file):
    rules = load_policy(json_policy_file)
    assert len(rules) == 1
    assert rules[0].severity_threshold == Severity.ERROR


def test_file_not_found_raises_policy_load_error(tmp_path):
    with pytest.raises(PolicyLoadError, match="not found"):
        load_policy(str(tmp_path / "missing.yaml"))


def test_unsupported_extension_raises_error(tmp_path):
    p = tmp_path / "policy.toml"
    p.write_text("[rules]")
    with pytest.raises(PolicyLoadError, match="Unsupported"):
        load_policy(str(p))


def test_missing_rules_key_raises_error(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("version: 1\n")
    with pytest.raises(PolicyLoadError, match="'rules'"):
        load_policy(str(p))


def test_invalid_severity_value_raises_error(tmp_path):
    p = tmp_path / "bad_sev.yaml"
    p.write_text("rules:\n  - name: x\n    severity_threshold: critical\n")
    with pytest.raises(PolicyLoadError, match="Invalid severity"):
        load_policy(str(p))


def test_invalid_change_type_raises_error(tmp_path):
    p = tmp_path / "bad_ct.yaml"
    p.write_text("rules:\n  - name: x\n    forbidden_change_types:\n      - vanished\n")
    with pytest.raises(PolicyLoadError, match="Invalid change_type"):
        load_policy(str(p))
