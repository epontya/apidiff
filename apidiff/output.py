"""High-level output orchestration: format selection, export, and stdout rendering."""

import sys
from typing import Optional
from apidiff.differ import DiffReport
from apidiff.formatter import render
from apidiff.exporter import export_report, detect_format_from_extension, ExportError


def resolve_format(fmt: Optional[str], output_path: Optional[str]) -> str:
    """Determine the output format from explicit flag or file extension."""
    if fmt:
        return fmt
    if output_path:
        detected = detect_format_from_extension(output_path)
        if detected:
            return detected
    return "text"


def output_report(
    report: DiffReport,
    fmt: Optional[str] = None,
    output_path: Optional[str] = None,
    color: bool = False,
    quiet: bool = False,
) -> None:
    """Render and/or export a report.

    - If *output_path* is given, write the report to that file.
    - Unless *quiet* is True, also print the text summary to stdout.

    Parameters
    ----------
    report:      The diff report to output.
    fmt:         Explicit format override ('text', 'json', 'markdown').
    output_path: Optional file path to write the report to.
    color:       Use ANSI colour in terminal output.
    quiet:       Suppress stdout output.
    """
    resolved_fmt = resolve_format(fmt, output_path)

    if output_path:
        try:
            export_report(report, output_path, fmt=resolved_fmt, color=False)
        except ExportError as exc:
            print(f"apidiff: export error: {exc}", file=sys.stderr)
            raise

    if not quiet:
        print(render(report, fmt="text", color=color))
