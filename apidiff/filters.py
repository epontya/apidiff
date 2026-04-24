"""Filtering utilities for DiffReport results."""

from typing import List, Optional
from apidiff.differ import DiffReport, Change, ChangeType, Severity


def filter_by_severity(report: DiffReport, severity: Severity) -> DiffReport:
    """Return a new DiffReport containing only changes at or above the given severity."""
    filtered = [
        change for change in report.changes
        if change.severity.value >= severity.value
    ]
    return DiffReport(changes=filtered)


def filter_by_change_type(report: DiffReport, change_type: ChangeType) -> DiffReport:
    """Return a new DiffReport containing only changes of the specified type."""
    filtered = [
        change for change in report.changes
        if change.change_type == change_type
    ]
    return DiffReport(changes=filtered)


def filter_by_path_prefix(report: DiffReport, prefix: str) -> DiffReport:
    """Return a new DiffReport containing only changes whose path starts with prefix."""
    filtered = [
        change for change in report.changes
        if change.path.startswith(prefix)
    ]
    return DiffReport(changes=filtered)


def filter_breaking_only(report: DiffReport) -> DiffReport:
    """Convenience wrapper: return only breaking changes."""
    return filter_by_severity(report, Severity.BREAKING)


def filter_non_breaking_only(report: DiffReport) -> DiffReport:
    """Convenience wrapper: return only non-breaking changes."""
    filtered = [
        change for change in report.changes
        if change.severity != Severity.BREAKING
    ]
    return DiffReport(changes=filtered)


def combine_reports(*reports: DiffReport) -> DiffReport:
    """Merge multiple DiffReports into a single DiffReport."""
    all_changes: List[Change] = []
    for report in reports:
        all_changes.extend(report.changes)
    return DiffReport(changes=all_changes)
