"""Tests for apidiff.annotation_formatter."""

import pytest

from apidiff.differ import Change, ChangeType, DiffReport, Severity
from apidiff.annotator import annotate_report
from apidiff.annotation_formatter import (
    format_annotated_text,
    format_annotated_markdown,
    render_annotated,
)


@pytest.fixture()
def annotated_mixed():
    report = DiffReport(
        version_old="1.0.0",
        version_new="2.0.0",
        changes=[
            Change(
                change_type=ChangeType.REMOVED_OPERATION,
                severity=Severity.BREAKING,
                path="/users",
                operation="delete",
                details={},
            ),
            Change(
                change_type=ChangeType.ADDED_PATH,
                severity=Severity.NON_BREAKING,
                path="/metrics",
                operation=None,
                details={},
            ),
        ],
    )
    return annotate_report(report)


@pytest.fixture()
def annotated_empty():
    return annotate_report(DiffReport(version_old="1.0", version_new="1.1", changes=[]))


def test_text_contains_version_header(annotated_mixed):
    out = format_annotated_text(annotated_mixed)
    assert "1.0.0" in out and "2.0.0" in out


def test_text_contains_path(annotated_mixed):
    out = format_annotated_text(annotated_mixed)
    assert "/users" in out


def test_text_contains_operation(annotated_mixed):
    out = format_annotated_text(annotated_mixed)
    assert "DELETE" in out


def test_text_empty_report_message(annotated_empty):
    out = format_annotated_text(annotated_empty)
    assert "No changes detected" in out


def test_markdown_contains_header(annotated_mixed):
    out = format_annotated_markdown(annotated_mixed)
    assert "##" in out
    assert "1.0.0" in out


def test_markdown_empty_report(annotated_empty):
    out = format_annotated_markdown(annotated_empty)
    assert "No changes detected" in out


def test_markdown_contains_effort_symbol(annotated_mixed):
    out = format_annotated_markdown(annotated_mixed)
    # high effort → 🔴, low effort → 🟢
    assert "🔴" in out
    assert "🟢" in out


def test_render_dispatches_text(annotated_mixed):
    out = render_annotated(annotated_mixed, fmt="text")
    assert "Migration Guide" in out


def test_render_dispatches_markdown(annotated_mixed):
    out = render_annotated(annotated_mixed, fmt="markdown")
    assert "##" in out


def test_render_defaults_to_text(annotated_mixed):
    out = render_annotated(annotated_mixed)
    assert "=" * 10 in out
