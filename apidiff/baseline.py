"""Baseline management: save and load a known-good diff report as a baseline
so that future runs can suppress already-acknowledged changes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from apidiff.differ import Change, ChangeType, DiffReport, Severity


class BaselineError(Exception):
    """Raised when a baseline file cannot be read or written."""


def _change_to_dict(change: Change) -> dict:
    return {
        "change_type": change.change_type.value,
        "severity": change.severity.value,
        "path": change.path,
        "method": change.method,
        "description": change.description,
    }


def _change_from_dict(data: dict) -> Change:
    return Change(
        change_type=ChangeType(data["change_type"]),
        severity=Severity(data["severity"]),
        path=data["path"],
        method=data.get("method"),
        description=data["description"],
    )


def save_baseline(report: DiffReport, filepath: str | Path) -> None:
    """Persist *report* changes to *filepath* as JSON."""
    filepath = Path(filepath)
    try:
        payload = {"changes": [_change_to_dict(c) for c in report.changes]}
        filepath.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        raise BaselineError(f"Cannot write baseline to {filepath}: {exc}") from exc


def load_baseline(filepath: str | Path) -> List[Change]:
    """Load previously saved baseline changes from *filepath*."""
    filepath = Path(filepath)
    if not filepath.exists():
        return []
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return [_change_from_dict(c) for c in data.get("changes", [])]
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        raise BaselineError(f"Cannot read baseline from {filepath}: {exc}") from exc


def suppress_baseline(report: DiffReport, baseline: List[Change]) -> DiffReport:
    """Return a new DiffReport with changes that appear in *baseline* removed."""
    baseline_keys = {
        (c.change_type, c.severity, c.path, c.method, c.description)
        for c in baseline
    }
    filtered = [
        c for c in report.changes
        if (c.change_type, c.severity, c.path, c.method, c.description)
        not in baseline_keys
    ]
    return DiffReport(changes=filtered)
