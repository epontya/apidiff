"""Export diff reports to files in various formats."""

import json
import os
from typing import Optional
from apidiff.differ import DiffReport
from apidiff.formatter import render
from apidiff.reporter import report_to_dict


SUPPORTED_FORMATS = ("text", "json", "markdown")


class ExportError(Exception):
    """Raised when a report cannot be exported."""


def export_report(
    report: DiffReport,
    output_path: str,
    fmt: str = "text",
    color: bool = False,
) -> None:
    """Write a DiffReport to *output_path* in the requested format.

    Parameters
    ----------
    report:      The diff report to export.
    output_path: Destination file path.
    fmt:         One of 'text', 'json', 'markdown'.
    color:       Include ANSI colour codes (text format only).
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ExportError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    try:
        if fmt == "json":
            content = json.dumps(report_to_dict(report), indent=2)
        else:
            content = render(report, fmt=fmt, color=color)

        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(content)
    except OSError as exc:
        raise ExportError(f"Failed to write report to '{output_path}': {exc}") from exc


def detect_format_from_extension(path: str) -> Optional[str]:
    """Infer the output format from the file extension."""
    ext = os.path.splitext(path)[-1].lower()
    mapping = {
        ".txt": "text",
        ".json": "json",
        ".md": "markdown",
        ".markdown": "markdown",
    }
    return mapping.get(ext)
