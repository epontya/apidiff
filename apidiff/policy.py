"""Load and apply validation policies from YAML/JSON config files."""

import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

from apidiff.differ import ChangeType
from apidiff.validator import ValidationRule
from apidiff.differ import Severity


class PolicyLoadError(Exception):
    """Raised when a policy file cannot be loaded or parsed."""


def load_policy(path: str) -> List[ValidationRule]:
    """Load a list of ValidationRule objects from a YAML or JSON policy file."""
    file_path = Path(path)
    if not file_path.exists():
        raise PolicyLoadError(f"Policy file not found: {path}")

    try:
        text = file_path.read_text(encoding="utf-8")
        if file_path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(text)
        elif file_path.suffix == ".json":
            data = json.loads(text)
        else:
            raise PolicyLoadError(f"Unsupported policy file format: {file_path.suffix}")
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise PolicyLoadError(f"Failed to parse policy file: {exc}") from exc

    if not isinstance(data, dict) or "rules" not in data:
        raise PolicyLoadError("Policy file must contain a top-level 'rules' key.")

    return [_parse_rule(r) for r in data["rules"]]


def _parse_rule(raw: Dict[str, Any]) -> ValidationRule:
    """Parse a single rule dict into a ValidationRule."""
    name = raw.get("name", "unnamed")
    description = raw.get("description", "")

    severity_threshold = None
    if "severity_threshold" in raw:
        try:
            severity_threshold = Severity(raw["severity_threshold"])
        except ValueError as exc:
            raise PolicyLoadError(f"Invalid severity value in rule '{name}': {exc}") from exc

    forbidden_change_types: List[ChangeType] = []
    for ct in raw.get("forbidden_change_types", []):
        try:
            forbidden_change_types.append(ChangeType(ct))
        except ValueError as exc:
            raise PolicyLoadError(
                f"Invalid change_type '{ct}' in rule '{name}': {exc}"
            ) from exc

    max_breaking = raw.get("max_breaking_changes")

    return ValidationRule(
        name=name,
        description=description,
        severity_threshold=severity_threshold,
        forbidden_change_types=forbidden_change_types,
        max_breaking_changes=max_breaking,
    )
