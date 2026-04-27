"""Format annotated diff reports as text or markdown."""

from apidiff.annotator import AnnotatedReport

_EFFORT_SYMBOL = {"low": "🟢", "medium": "🟡", "high": "🔴"}


def format_annotated_text(report: AnnotatedReport) -> str:
    """Render annotated report as plain text."""
    lines = [
        f"Migration Guide: {report.version_old} → {report.version_new}",
        "=" * 60,
    ]
    if report.is_empty():
        lines.append("No changes detected.")
        return "\n".join(lines)

    for ac in report.annotated:
        severity = ac.change.severity.value.upper()
        effort = ac.migration_effort.upper()
        lines.append(f"[{severity}] {ac.change.change_type.value}")
        lines.append(f"  Path      : {ac.change.path}")
        if ac.change.operation:
            lines.append(f"  Operation : {ac.change.operation.upper()}")
        lines.append(f"  Effort    : {effort}")
        lines.append(f"  Hint      : {ac.hint}")
        lines.append("")
    return "\n".join(lines)


def format_annotated_markdown(report: AnnotatedReport) -> str:
    """Render annotated report as Markdown."""
    lines = [
        f"## Migration Guide: `{report.version_old}` → `{report.version_new}`",
        "",
    ]
    if report.is_empty():
        lines.append("_No changes detected._")
        return "\n".join(lines)

    for ac in report.annotated:
        symbol = _EFFORT_SYMBOL.get(ac.migration_effort, "⚪")
        lines.append(f"### {symbol} `{ac.change.change_type.value}`")
        lines.append(f"- **Path**: `{ac.change.path}`")
        if ac.change.operation:
            lines.append(f"- **Operation**: `{ac.change.operation.upper()}`")
        lines.append(f"- **Severity**: `{ac.change.severity.value}`")
        lines.append(f"- **Migration effort**: `{ac.migration_effort}`")
        lines.append(f"- **Hint**: {ac.hint}")
        lines.append("")
    return "\n".join(lines)


def render_annotated(report: AnnotatedReport, fmt: str = "text") -> str:
    """Dispatch to the correct formatter."""
    if fmt == "markdown":
        return format_annotated_markdown(report)
    return format_annotated_text(report)
