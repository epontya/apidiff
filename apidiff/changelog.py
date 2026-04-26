"""Generates a human-readable changelog from a DiffReport."""

from dataclasses import dataclass, field
from typing import List, Optional
from apidiff.differ import DiffReport, Change, Severity, ChangeType


@dataclass
class ChangelogEntry:
    version: str
    breaking: List[Change] = field(default_factory=list)
    non_breaking: List[Change] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.breaking and not self.non_breaking


def build_changelog_entry(report: DiffReport, version: str) -> ChangelogEntry:
    """Build a ChangelogEntry from a DiffReport for a given version label."""
    entry = ChangelogEntry(version=version)
    for change in report.changes:
        if change.severity == Severity.BREAKING:
            entry.breaking.append(change)
        else:
            entry.non_breaking.append(change)
    return entry


def format_changelog(entry: ChangelogEntry, include_non_breaking: bool = True) -> str:
    """Render a ChangelogEntry as a markdown-style string."""
    lines: List[str] = []
    lines.append(f"## {entry.version}")
    lines.append("")

    if entry.breaking:
        lines.append("### Breaking Changes")
        for change in entry.breaking:
            lines.append(f"- [{change.change_type.value}] `{change.path}`: {change.description}")
        lines.append("")

    if include_non_breaking and entry.non_breaking:
        lines.append("### Non-Breaking Changes")
        for change in entry.non_breaking:
            lines.append(f"- [{change.change_type.value}] `{change.path}`: {change.description}")
        lines.append("")

    if entry.is_empty():
        lines.append("_No changes detected._")
        lines.append("")

    return "\n".join(lines)


def write_changelog(entry: ChangelogEntry, path: str, include_non_breaking: bool = True) -> None:
    """Write a formatted changelog entry to a file."""
    content = format_changelog(entry, include_non_breaking=include_non_breaking)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
