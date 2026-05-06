"""CLI command for diffing OpenAPI operation tags."""

from __future__ import annotations

import argparse
import sys

from apidiff.differ_tags import diff_tags
from apidiff.formatter import render
from apidiff.loader import SpecLoadError, load_spec
from apidiff.summary import summarize


def build_tags_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "tags",
        help="Diff operation tags between two OpenAPI specs.",
    )
    parser.add_argument("old", help="Path to the old OpenAPI spec.")
    parser.add_argument("new", help="Path to the new OpenAPI spec.")
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary line after the diff.",
    )
    return parser


def run_tags(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_tags(old_spec, new_spec)
    print(render(report, fmt=args.fmt))

    if args.summary:
        s = summarize(report)
        print(f"\nSummary: {s.total} change(s), {s.breaking} breaking, {s.non_breaking} non-breaking.")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="apidiff-tags", description="Diff OpenAPI operation tags.")
    subparsers = parser.add_subparsers(dest="command")
    build_tags_parser(subparsers)
    args = parser.parse_args()
    if args.command is None:
        # allow direct invocation without subcommand by re-parsing as flat args
        parser2 = argparse.ArgumentParser(prog="apidiff-tags")
        parser2.add_argument("old")
        parser2.add_argument("new")
        parser2.add_argument("--format", choices=["text", "markdown", "json"], default="text", dest="fmt")
        parser2.add_argument("--summary", action="store_true")
        args = parser2.parse_args()
    sys.exit(run_tags(args))


if __name__ == "__main__":
    main()
