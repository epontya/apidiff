"""Groups diff report changes by tag, path prefix, or severity for structured analysis."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from apidiff.differ import Change, DiffReport, Severity


@dataclass
class GroupedReport:
    old_version: str
    new_version: str
    groups: Dict[str, List[Change]] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return all(len(v) == 0 for v in self.groups.values())

    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    def changes_for(self, group: str) -> List[Change]:
        return self.groups.get(group, [])


def group_by_severity(report: DiffReport) -> GroupedReport:
    """Group changes by their severity label."""
    buckets: Dict[str, List[Change]] = defaultdict(list)
    for change in report.changes:
        buckets[change.severity.value].append(change)
    return GroupedReport(
        old_version=report.old_version,
        new_version=report.new_version,
        groups=dict(buckets),
    )


def group_by_path_prefix(report: DiffReport, depth: int = 1) -> GroupedReport:
    """Group changes by the first *depth* segments of the API path."""
    buckets: Dict[str, List[Change]] = defaultdict(list)
    for change in report.changes:
        parts = [p for p in change.path.split("/") if p]
        prefix = "/" + "/".join(parts[:depth]) if parts else "/"
        buckets[prefix].append(change)
    return GroupedReport(
        old_version=report.old_version,
        new_version=report.new_version,
        groups=dict(buckets),
    )


def group_by_change_type(report: DiffReport) -> GroupedReport:
    """Group changes by their change_type string."""
    buckets: Dict[str, List[Change]] = defaultdict(list)
    for change in report.changes:
        buckets[change.change_type.value].append(change)
    return GroupedReport(
        old_version=report.old_version,
        new_version=report.new_version,
        groups=dict(buckets),
    )


def grouped_report_to_dict(grouped: GroupedReport) -> dict:
    """Serialize a GroupedReport to a plain dictionary."""
    return {
        "old_version": grouped.old_version,
        "new_version": grouped.new_version,
        "groups": {
            key: [
                {
                    "path": c.path,
                    "operation": c.operation,
                    "change_type": c.change_type.value,
                    "severity": c.severity.value,
                    "description": c.description,
                }
                for c in changes
            ]
            for key, changes in grouped.groups.items()
        },
    }
