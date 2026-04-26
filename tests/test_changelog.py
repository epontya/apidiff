"""Tests for apidiff.changelog module."""

import os
import pytest
from apidiff.differ import DiffReport, Change, ChangeType, Severity
from apidiff.changelog import (
    build_changelog_entry,
    format_changelog,
    write_changelog,
    ChangelogEntry,
)


@pytest.fixture
def mixed_report():
    return DiffReport(
        changes=[
            Change(
                path="/users",
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                description="Path /users was removed",
            ),
            Change(
                path="/items",
                change_type=ChangeType.ADDED,
                severity=Severity.NON_BREAKING,
                description="Path /items was added",
            ),
        ]
    )


@pytest.fixture
def empty_report():
    return DiffReport(changes=[])


def test_build_changelog_entry_version_label(mixed_report):
    entry = build_changelog_entry(mixed_report, version="v2.0.0")
    assert entry.version == "v2.0.0"


def test_build_changelog_entry_breaking_count(mixed_report):
    entry = build_changelog_entry(mixed_report, version="v2.0.0")
    assert len(entry.breaking) == 1
    assert entry.breaking[0].path == "/users"


def test_build_changelog_entry_non_breaking_count(mixed_report):
    entry = build_changelog_entry(mixed_report, version="v2.0.0")
    assert len(entry.non_breaking) == 1
    assert entry.non_breaking[0].path == "/items"


def test_empty_report_entry_is_empty(empty_report):
    entry = build_changelog_entry(empty_report, version="v1.1.0")
    assert entry.is_empty()


def test_format_changelog_contains_version(mixed_report):
    entry = build_changelog_entry(mixed_report, version="v2.0.0")
    output = format_changelog(entry)
    assert "## v2.0.0" in output


def test_format_changelog_contains_breaking_section(mixed_report):
    entry = build_changelog_entry(mixed_report, version="v2.0.0")
    output = format_changelog(entry)
    assert "### Breaking Changes" in output
    assert "/users" in output


def test_format_changelog_contains_non_breaking_section(mixed_report):
    entry = build_changelog_entry(mixed_report, version="v2.0.0")
    output = format_changelog(entry)
    assert "### Non-Breaking Changes" in output
    assert "/items" in output


def test_format_changelog_excludes_non_breaking_when_flag_false(mixed_report):
    entry = build_changelog_entry(mixed_report, version="v2.0.0")
    output = format_changelog(entry, include_non_breaking=False)
    assert "### Non-Breaking Changes" not in output
    assert "/items" not in output


def test_format_changelog_empty_report_message(empty_report):
    entry = build_changelog_entry(empty_report, version="v1.0.1")
    output = format_changelog(entry)
    assert "_No changes detected._" in output


def test_write_changelog_creates_file(tmp_path, mixed_report):
    out_file = str(tmp_path / "CHANGELOG.md")
    entry = build_changelog_entry(mixed_report, version="v3.0.0")
    write_changelog(entry, out_file)
    assert os.path.exists(out_file)


def test_write_changelog_content(tmp_path, mixed_report):
    out_file = str(tmp_path / "CHANGELOG.md")
    entry = build_changelog_entry(mixed_report, version="v3.0.0")
    write_changelog(entry, out_file)
    content = open(out_file).read()
    assert "## v3.0.0" in content
    assert "/users" in content
