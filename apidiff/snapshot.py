"""Snapshot helpers: capture the current spec state so it can be diffed later."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from apidiff.loader import load_spec


class SnapshotError(Exception):
    """Raised when a snapshot cannot be saved or loaded."""


def save_snapshot(spec_path: str | Path, snapshot_path: str | Path) -> None:
    """Load *spec_path* and persist it as a JSON snapshot to *snapshot_path*."""
    spec = load_spec(str(spec_path))
    snapshot_path = Path(snapshot_path)
    try:
        snapshot_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    except OSError as exc:
        raise SnapshotError(
            f"Cannot write snapshot to {snapshot_path}: {exc}"
        ) from exc


def load_snapshot(snapshot_path: str | Path) -> Dict[str, Any]:
    """Load a previously saved snapshot from *snapshot_path*."""
    snapshot_path = Path(snapshot_path)
    if not snapshot_path.exists():
        raise SnapshotError(f"Snapshot file not found: {snapshot_path}")
    try:
        return json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(
            f"Cannot read snapshot from {snapshot_path}: {exc}"
        ) from exc


def snapshot_exists(snapshot_path: str | Path) -> bool:
    """Return True if a snapshot file exists at *snapshot_path*."""
    return Path(snapshot_path).exists()
