"""Trace which changes affect a specific operation or path pattern."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import List, Optional

from apidiff.differ import Change, DiffReport, Severity


@dataclass
class TraceResult:
    old_version: str
    new_version: str
    pattern: str
    matched: List[Change] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.matched) == 0

    def has_breaking(self) -> bool:
        return any(c.severity == Severity.BREAKING for c in self.matched)

    def breaking_changes(self) -> List[Change]:
        return [c for c in self.matched if c.severity == Severity.BREAKING]

    def non_breaking_changes(self) -> List[Change]:
        return [c for c in self.matched if c.severity == Severity.NON_BREAKING]


def trace_changes(
    report: DiffReport,
    pattern: str,
    operation: Optional[str] = None,
) -> TraceResult:
    """Return all changes whose path matches *pattern* (glob-style).

    Optionally filter further by HTTP *operation* (e.g. ``"get"``).
    """
    result = TraceResult(
        old_version=report.old_version,
        new_version=report.new_version,
        pattern=pattern,
    )

    for change in report.changes:
        path_part = change.path.split(".")[0] if "." in change.path else change.path
        if not fnmatch.fnmatch(path_part, pattern):
            continue
        if operation is not None:
            op_in_path = change.path.split(".")[1] if "." in change.path else ""
            if op_in_path.lower() != operation.lower():
                continue
        result.matched.append(change)

    return result


def format_trace(result: TraceResult) -> str:
    """Render a TraceResult as human-readable text."""
    lines: List[str] = [
        f"Trace: {result.pattern}",
        f"Versions: {result.old_version} -> {result.new_version}",
        f"Matched changes: {len(result.matched)}",
        "",
    ]
    if result.is_empty():
        lines.append("  (no changes matched)")
    else:
        for change in result.matched:
            marker = "[BREAKING]" if change.severity == Severity.BREAKING else "[non-breaking]"
            lines.append(f"  {marker} {change.path}: {change.description}")
    return "\n".join(lines)
