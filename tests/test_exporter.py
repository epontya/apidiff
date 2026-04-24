"""Tests for apidiff.exporter module."""

import json
import os
import pytest
from apidiff.differ import DiffReport, Change, ChangeType, Severity
from apidiff.exporter import export_report, detect_format_from_extension, ExportError


@pytest.fixture
def simple_report():
    return DiffReport(
        changes=[
            Change(
                path="/pets",
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                description="Endpoint removed",
            )
        ]
    )


@pytest.fixture
def empty_report():
    return DiffReport(changes=[])


def test_export_text_creates_file(tmp_path, simple_report):
    out = tmp_path / "report.txt"
    export_report(simple_report, str(out), fmt="text")
    assert out.exists()


def test_export_text_content(tmp_path, simple_report):
    out = tmp_path / "report.txt"
    export_report(simple_report, str(out), fmt="text")
    content = out.read_text()
    assert "/pets" in content
    assert "BREAKING" in content


def test_export_json_creates_file(tmp_path, simple_report):
    out = tmp_path / "report.json"
    export_report(simple_report, str(out), fmt="json")
    assert out.exists()


def test_export_json_is_valid_json(tmp_path, simple_report):
    out = tmp_path / "report.json"
    export_report(simple_report, str(out), fmt="json")
    data = json.loads(out.read_text())
    assert isinstance(data, dict)


def test_export_markdown_creates_file(tmp_path, simple_report):
    out = tmp_path / "report.md"
    export_report(simple_report, str(out), fmt="markdown")
    assert out.exists()


def test_export_markdown_content(tmp_path, simple_report):
    out = tmp_path / "report.md"
    export_report(simple_report, str(out), fmt="markdown")
    content = out.read_text()
    assert "## API Diff Report" in content


def test_export_unsupported_format_raises(tmp_path, simple_report):
    with pytest.raises(ExportError, match="Unsupported format"):
        export_report(simple_report, str(tmp_path / "out.xml"), fmt="xml")


def test_export_creates_nested_dirs(tmp_path, simple_report):
    out = tmp_path / "nested" / "deep" / "report.txt"
    export_report(simple_report, str(out), fmt="text")
    assert out.exists()


def test_detect_format_txt():
    assert detect_format_from_extension("report.txt") == "text"


def test_detect_format_json():
    assert detect_format_from_extension("output.json") == "json"


def test_detect_format_md():
    assert detect_format_from_extension("changes.md") == "markdown"


def test_detect_format_markdown_extension():
    assert detect_format_from_extension("report.markdown") == "markdown"


def test_detect_format_unknown_returns_none():
    assert detect_format_from_extension("report.csv") is None
