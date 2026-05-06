"""CLI command for diffing pattern constraints between two OpenAPI specs."""

from __future__ import annotations

import argparse
import sys

from apidiff.loader import SpecLoadError, load_spec
from apidiff.differ_extensions_patterns import diff_patterns
from apidiff.formatter import render
from apidiff.filters import filter_breaking_only


def build_patterns_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "patterns",
        help="Diff pattern/regex constraints on schema properties.",
    )
    parser.add_argument("old", help="Path to the old OpenAPI spec.")
    parser.add_argument("new", help="Path to the new OpenAPI spec.")
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        dest="fmt",
    )
    parser.add_argument(
        "--breaking-only",
        action="store_true",
        default=False,
        help="Only show breaking changes.",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        default=False,
        help="Exit with code 1 if breaking changes are found.",
    )
    return parser


def run_patterns(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_patterns(old_spec, new_spec)

    if args.breaking_only:
        report = filter_breaking_only(report)

    output = render(report, fmt=args.fmt)
    print(output)

    if args.fail_on_breaking and any(
        c.severity.value == "breaking" for c in report.changes
    ):
        return 1

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Diff pattern constraints in OpenAPI specs.")
    subparsers = parser.add_subparsers(dest="command")
    build_patterns_parser(subparsers)
    args = parser.parse_args()
    sys.exit(run_patterns(args))


if __name__ == "__main__":
    main()
