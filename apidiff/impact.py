"""Impact analysis for API diff reports.

Provides tooling to assess the potential impact of detected changes
on API consumers, categorising changes by their likely blast radius.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from apidiff.differ import DiffReport, Change, ChangeType, Severity


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ImpactedArea:
    """Represents a single API area and the changes that affect it."""

    path: str
    operations: List[str] = field(default_factory=list)
    changes: List[Change] = field(default_factory=list)

    @property
    def has_breaking(self) -> bool:
        return any(c.severity == Severity.BREAKING for c in self.changes)


@dataclass
class ImpactReport:
    """Aggregated impact analysis derived from a DiffReport."""

    old_version: str
    new_version: str
    impacted_areas: List[ImpactedArea] = field(default_factory=list)
    # Counts by severity
    breaking_count: int = 0
    non_breaking_count: int = 0

    @property
    def is_empty(self) -> bool:
        return len(self.impacted_areas) == 0

    @property
    def total_impacted_paths(self) -> int:
        return len(self.impacted_areas)


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def _group_changes_by_path(changes: List[Change]) -> Dict[str, List[Change]]:
    """Group a flat list of changes by their API path."""
    grouped: Dict[str, List[Change]] = {}
    for change in changes:
        key = change.path or "(unknown)"
        grouped.setdefault(key, []).append(change)
    return grouped


def analyse_impact(report: DiffReport) -> ImpactReport:
    """Analyse a DiffReport and return an ImpactReport.

    Each distinct API path mentioned in the diff becomes an ImpactedArea.
    Operations are inferred from the change description where possible.

    Args:
        report: The diff report produced by the differ.

    Returns:
        An ImpactReport summarising which areas of the API are affected.
    """
    all_changes = report.changes
    grouped = _group_changes_by_path(all_changes)

    areas: List[ImpactedArea] = []
    for path, changes in sorted(grouped.items()):
        # Collect unique HTTP operations referenced in change descriptions
        operations: List[str] = []
        for change in changes:
            if change.operation and change.operation not in operations:
                operations.append(change.operation)

        areas.append(
            ImpactedArea(
                path=path,
                operations=operations,
                changes=changes,
            )
        )

    breaking = sum(1 for c in all_changes if c.severity == Severity.BREAKING)
    non_breaking = sum(1 for c in all_changes if c.severity == Severity.NON_BREAKING)

    return ImpactReport(
        old_version=report.old_version,
        new_version=report.new_version,
        impacted_areas=areas,
        breaking_count=breaking,
        non_breaking_count=non_breaking,
    )


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_impact_text(impact: ImpactReport) -> str:
    """Render an ImpactReport as a human-readable text string."""
    lines: List[str] = [
        f"Impact Analysis: {impact.old_version} → {impact.new_version}",
        f"Impacted paths : {impact.total_impacted_paths}",
        f"Breaking       : {impact.breaking_count}",
        f"Non-breaking   : {impact.non_breaking_count}",
        "",
    ]

    if impact.is_empty:
        lines.append("No impacted areas detected.")
        return "\n".join(lines)

    for area in impact.impacted_areas:
        severity_marker = "[BREAKING]" if area.has_breaking else "[safe]"
        ops = ", ".join(area.operations) if area.operations else "n/a"
        lines.append(f"  {severity_marker} {area.path}  (operations: {ops})")
        for change in area.changes:
            lines.append(f"    - [{change.change_type.value}] {change.description}")

    return "\n".join(lines)
