"""Loads and validates OpenAPI spec files (JSON or YAML)."""

import json
import os
from typing import Any, Dict

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class SpecLoadError(Exception):
    """Raised when an OpenAPI spec cannot be loaded or parsed."""


def load_spec(path: str) -> Dict[str, Any]:
    """Load an OpenAPI spec from a JSON or YAML file.

    Args:
        path: Filesystem path to the spec file.

    Returns:
        Parsed spec as a dictionary.

    Raises:
        SpecLoadError: If the file cannot be read or parsed.
    """
    if not os.path.isfile(path):
        raise SpecLoadError(f"File not found: {path}")

    _, ext = os.path.splitext(path)
    ext = ext.lower()

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        raise SpecLoadError(f"Cannot read file '{path}': {exc}") from exc

    if ext in (".yaml", ".yml"):
        if not HAS_YAML:
            raise SpecLoadError(
                "PyYAML is required to load YAML specs. "
                "Install it with: pip install pyyaml"
            )
        try:
            spec = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise SpecLoadError(f"YAML parse error in '{path}': {exc}") from exc
    elif ext == ".json":
        try:
            spec = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SpecLoadError(f"JSON parse error in '{path}': {exc}") from exc
    else:
        raise SpecLoadError(
            f"Unsupported file extension '{ext}'. Expected .json, .yaml, or .yml."
        )

    if not isinstance(spec, dict):
        raise SpecLoadError(f"Spec in '{path}' must be a JSON/YAML object, got {type(spec).__name__}.")

    _validate_required_fields(spec, path)
    return spec


def _validate_required_fields(spec: Dict[str, Any], path: str) -> None:
    """Ensure the spec contains the minimum required OpenAPI fields."""
    if "openapi" not in spec and "swagger" not in spec:
        raise SpecLoadError(
            f"'{path}' does not appear to be a valid OpenAPI/Swagger spec "
            "(missing 'openapi' or 'swagger' field)."
        )
    if "info" not in spec:
        raise SpecLoadError(f"'{path}' is missing required 'info' field.")
    if "paths" not in spec:
        raise SpecLoadError(f"'{path}' is missing required 'paths' field.")
