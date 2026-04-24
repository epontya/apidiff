"""Tests for apidiff.formatter module."""

import pytest
from apidiff.differ import DiffReport, Change, ChangeType, Severity
from apidiff.formatter import format_text, format_markdown, render


@pytest.fixture
def empty_report():
    return DiffReport(changes=[])


@pytest.fixture
def mixed_report():
    return DiffReport(
        changes=[
            Change(
                path="/users",
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                description="Path removed",
            ),
            Change(
                path="/items",
                change_type=ChangeType.ADDED,
                severity=Severity.NON_BREAKING,
                description="New path added",
            ),
        ]
    )


def test_format_text_empty_report(empty_report):
    output = format_text(empty_report)
    assert "No changes detected." in output


def test_format_text_contains_severity(mixed_report):
    output = format_text(mixed_report)
    assert "BREAKING" in output
    assert "NON_BREAKING" in output


def test_format_text_contains_path(mixed_report):
    output = format_text(mixed_report)
    assert "/users" in output
    assert "/items" in output


def test_format_text_contains_description(mixed_report):
    output = format_text(mixed_report)
    assert "Path removed" in output
    assert "New path added" in output


def test_format_text_color_includes_ansi(mixed_report):
    output = format_text(mixed_report, color=True)
    assert "\033[" in output


def test_format_text_no_color_excludes_ansi(mixed_report):
    output = format_text(mixed_report, color=False)
    assert "\033[" not in output


def test_format_markdown_header(mixed_report):
    output = format_markdown(mixed_report)
    assert "## API Diff Report" in output


def test_format_markdown_table_row(mixed_report):
    output = format_markdown(mixed_report)
    assert "`/users`" in output
    assert "`/items`" in output


def test_format_markdown_empty_report(empty_report):
    output = format_markdown(empty_report)
    assert "_No changes detected._" in output


def test_render_dispatches_markdown(mixed_report):
    output = render(mixed_report, fmt="markdown")
    assert "## API Diff Report" in output


def test_render_dispatches_text(mixed_report):
    output = render(mixed_report, fmt="text")
    assert "BREAKING" in output


def test_render_default_is_text(mixed_report):
    output = render(mixed_report)
    assert "BREAKING" in output
    assert "## API Diff Report" not in output
