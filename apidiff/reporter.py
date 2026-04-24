"""Formats and outputs a DiffReport in various formats."""

import json
from typing import TextIO

from apidiff.differ import DiffReport


def report_to_dict(report: DiffReport) -> dict:
    """Serialize a DiffReport to a plain dictionary."""
    return {
        "summary": report.summary(),
        "changes": [
            {
                "path": c.path,
                "change_type": c.change_type.value,
                "severity": c.severity.value,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "description": c.description,
            }
            for c in report.changes
        ],
    }


def report_to_json(report: DiffReport, indent: int = 2) -> str:
    """Serialize a DiffReport to a JSON string."""
    return json.dumps(report_to_dict(report), indent=indent, default=str)


def report_to_text(report: DiffReport) -> str:
    """Format a DiffReport as a human-readable text summary."""
    lines = []
    summary = report.summary()
    lines.append("=" * 50)
    lines.append("API Diff Report")
    lines.append("=" * 50)
    lines.append(
        f"Total changes : {summary['total']}"
    )
    lines.append(
        f"Breaking      : {summary['breaking']}"
    )
    lines.append(
        f"Non-breaking  : {summary['non_breaking']}"
    )
    lines.append(
        f"Info          : {summary['info']}"
    )
    lines.append("")

    if not report.changes:
        lines.append("No changes detected.")
        return "\n".join(lines)

    severity_order = {"breaking": 0, "non-breaking": 1, "info": 2}
    sorted_changes = sorted(
        report.changes, key=lambda c: severity_order.get(c.severity.value, 99)
    )

    for change in sorted_changes:
        severity_label = change.severity.value.upper()
        lines.append(
            f"[{severity_label}] ({change.change_type.value}) {change.description}"
        )
        lines.append(f"  path: {change.path}")
        if change.old_value is not None:
            lines.append(f"  old : {change.old_value}")
        if change.new_value is not None:
            lines.append(f"  new : {change.new_value}")
        lines.append("")

    return "\n".join(lines)


def write_report(
    report: DiffReport, fmt: str = "text", stream: TextIO | None = None
) -> str:
    """Write a formatted report to a stream (or return as string)."""
    if fmt == "json":
        output = report_to_json(report)
    elif fmt == "text":
        output = report_to_text(report)
    else:
        raise ValueError(f"Unsupported format: '{fmt}'. Choose 'text' or 'json'.")

    if stream is not None:
        stream.write(output)

    return output
