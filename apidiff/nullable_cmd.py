"""CLI sub-command: detect nullable flag changes between two OpenAPI specs."""
from __future__ import annotations

import argparse
import sys

from apidiff.differ_extensions_nullable import diff_nullable
from apidiff.formatter import render
from apidiff.loader import SpecLoadError, load_spec


def build_nullable_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "nullable",
        help="Detect nullable flag changes in component schema properties.",
    )
    parser.add_argument("old", help="Path to the old OpenAPI spec (JSON or YAML).")
    parser.add_argument("new", help="Path to the new OpenAPI spec (JSON or YAML).")
    parser.add_argument(
        "--format",
        choices=["text", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        default=False,
        help="Exit with code 1 when breaking nullable changes are found.",
    )
    return parser


def run_nullable(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_nullable(old_spec, new_spec)
    print(render(report, fmt=args.format))

    if args.fail_on_breaking:
        from apidiff.differ import Severity

        has_breaking = any(
            c.severity == Severity.BREAKING for c in report.changes
        )
        return 1 if has_breaking else 0

    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        prog="apidiff-nullable",
        description="Detect nullable flag changes in OpenAPI schemas.",
    )
    subparsers = parser.add_subparsers(dest="command")
    build_nullable_parser(subparsers)
    args = parser.parse_args()
    sys.exit(run_nullable(args))
