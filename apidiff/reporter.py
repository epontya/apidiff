"""Output formatting and writing for DiffReport results."""

import json
import sys
from typing import Optional
from apidiff.differ import DiffReport, Change
from apidiff.summary import summarize, format_summary


def report_to_dict(report: DiffReport) -> dict:
    """Serialize a DiffReport to a plain dictionary."""
    return {
        "summary": summarize(report).as_dict(),
        "changes": [
            {
                "path": c.path,
                "change_type": c.change_type.value,
                "severity": c.severity.value,
                "description": c.description,
            }
            for c in report.changes
        ],
    }


def report_to_json(report: DiffReport, indent: int = 2) -> str:
    """Serialize a DiffReport to a JSON string."""
    return json.dumps(report_to_dict(report), indent=indent)


def report_to_text(report: DiffReport) -> str:
    """Format a DiffReport as human-readable text."""
    lines = []
    summary = summarize(report)
    lines.append(format_summary(summary))

    if report.changes:
        lines.append("\nChanges:")
        for change in report.changes:
            severity_tag = "[BREAKING]" if change.severity.value == "breaking" else "[non-breaking]"
            lines.append(f"  {severity_tag} {change.change_type.value.upper()} {change.path}")
            lines.append(f"    {change.description}")
    else:
        lines.append("\nNo changes detected.")

    return "\n".join(lines)


def write_report(
    report: DiffReport,
    fmt: str = "text",
    output_path: Optional[str] = None,
) -> None:
    """Write a formatted report to a file or stdout."""
    if fmt == "json":
        content = report_to_json(report)
    else:
        content = report_to_text(report)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.write("\n")
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")
