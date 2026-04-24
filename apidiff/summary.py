"""Summary statistics for a DiffReport."""

from dataclasses import dataclass, field
from typing import Dict
from apidiff.differ import DiffReport, ChangeType, Severity


@dataclass
class DiffSummary:
    total: int = 0
    breaking: int = 0
    non_breaking: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "breaking": self.breaking,
            "non_breaking": self.non_breaking,
            "by_type": self.by_type,
        }


def summarize(report: DiffReport) -> DiffSummary:
    """Compute summary statistics from a DiffReport."""
    summary = DiffSummary()
    summary.total = len(report.changes)

    for change in report.changes:
        if change.severity == Severity.BREAKING:
            summary.breaking += 1
        else:
            summary.non_breaking += 1

        type_key = change.change_type.value
        summary.by_type[type_key] = summary.by_type.get(type_key, 0) + 1

    return summary


def format_summary(summary: DiffSummary) -> str:
    """Return a human-readable summary string."""
    lines = [
        f"Total changes : {summary.total}",
        f"  Breaking    : {summary.breaking}",
        f"  Non-breaking: {summary.non_breaking}",
        "  By type:",
    ]
    for change_type, count in sorted(summary.by_type.items()):
        lines.append(f"    {change_type:<12}: {count}")
    return "\n".join(lines)
