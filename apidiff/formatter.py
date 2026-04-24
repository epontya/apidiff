"""Formatters for rendering diff reports in multiple output formats."""

from typing import Optional
from apidiff.differ import DiffReport, Severity
from apidiff.summary import summarize, format_summary


ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_GREEN = "\033[92m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


def _severity_color(severity: Severity) -> str:
    if severity == Severity.BREAKING:
        return ANSI_RED
    elif severity == Severity.NON_BREAKING:
        return ANSI_GREEN
    return ANSI_YELLOW


def format_text(report: DiffReport, color: bool = False) -> str:
    """Render a DiffReport as a human-readable text string."""
    lines = []
    summary = summarize(report)
    lines.append(format_summary(summary))
    lines.append("")

    if not report.changes:
        lines.append("No changes detected.")
        return "\n".join(lines)

    for change in report.changes:
        severity_label = change.severity.value.upper()
        if color:
            col = _severity_color(change.severity)
            severity_label = f"{col}{ANSI_BOLD}{severity_label}{ANSI_RESET}"
        line = f"[{severity_label}] {change.change_type.value}: {change.path}"
        if change.description:
            line += f" — {change.description}"
        lines.append(line)

    return "\n".join(lines)


def format_markdown(report: DiffReport) -> str:
    """Render a DiffReport as a Markdown string."""
    lines = []
    summary = summarize(report)
    lines.append("## API Diff Report")
    lines.append("")
    lines.append(f"- **Total changes:** {summary.total}")
    lines.append(f"- **Breaking:** {summary.breaking_count}")
    lines.append(f"- **Non-breaking:** {summary.non_breaking_count}")
    lines.append("")

    if not report.changes:
        lines.append("_No changes detected._")
        return "\n".join(lines)

    lines.append("| Severity | Type | Path | Description |")
    lines.append("|----------|------|------|-------------|")
    for change in report.changes:
        desc = change.description or ""
        lines.append(
            f"| {change.severity.value} | {change.change_type.value} "
            f"| `{change.path}` | {desc} |"
        )

    return "\n".join(lines)


def render(report: DiffReport, fmt: str = "text", color: bool = False) -> str:
    """Dispatch rendering to the appropriate formatter."""
    if fmt == "markdown":
        return format_markdown(report)
    return format_text(report, color=color)
