"""Compute statistics over a DiffReport for trend analysis and reporting."""

from dataclasses import dataclass, field
from typing import Dict, List

from apidiff.differ import DiffReport, ChangeType, Severity


@dataclass
class DiffStats:
    total: int = 0
    breaking: int = 0
    non_breaking: int = 0
    by_severity: Dict[str, int] = field(default_factory=dict)
    by_change_type: Dict[str, int] = field(default_factory=dict)
    affected_paths: List[str] = field(default_factory=list)
    breaking_ratio: float = 0.0


def compute_stats(report: DiffReport) -> DiffStats:
    """Compute statistics from a DiffReport."""
    stats = DiffStats()
    stats.total = len(report.changes)

    seen_paths: set = set()

    for change in report.changes:
        if change.breaking:
            stats.breaking += 1
        else:
            stats.non_breaking += 1

        sev_key = change.severity.value
        stats.by_severity[sev_key] = stats.by_severity.get(sev_key, 0) + 1

        ct_key = change.change_type.value
        stats.by_change_type[ct_key] = stats.by_change_type.get(ct_key, 0) + 1

        if change.path and change.path not in seen_paths:
            seen_paths.add(change.path)
            stats.affected_paths.append(change.path)

    if stats.total > 0:
        stats.breaking_ratio = round(stats.breaking / stats.total, 4)

    return stats


def stats_to_dict(stats: DiffStats) -> dict:
    """Serialize DiffStats to a plain dictionary."""
    return {
        "total": stats.total,
        "breaking": stats.breaking,
        "non_breaking": stats.non_breaking,
        "breaking_ratio": stats.breaking_ratio,
        "by_severity": stats.by_severity,
        "by_change_type": stats.by_change_type,
        "affected_paths": stats.affected_paths,
    }


def format_stats(stats: DiffStats) -> str:
    """Return a human-readable string summary of stats."""
    lines = [
        f"Total changes   : {stats.total}",
        f"Breaking        : {stats.breaking}",
        f"Non-breaking    : {stats.non_breaking}",
        f"Breaking ratio  : {stats.breaking_ratio:.1%}",
        "By severity     : "
        + ", ".join(f"{k}={v}" for k, v in sorted(stats.by_severity.items())),
        "By change type  : "
        + ", ".join(f"{k}={v}" for k, v in sorted(stats.by_change_type.items())),
        f"Affected paths  : {len(stats.affected_paths)}",
    ]
    return "\n".join(lines)
