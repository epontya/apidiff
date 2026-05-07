"""CLI sub-command: diff discriminator mappings between two OpenAPI specs."""
from __future__ import annotations

import argparse
import sys

from apidiff.differ_extensions_discriminator import diff_discriminator
from apidiff.filters import filter_breaking_only
from apidiff.formatter import render
from apidiff.loader import SpecLoadError, load_spec


def build_discriminator_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "discriminator",
        help="Diff discriminator mappings in component schemas",
    )
    parser.add_argument("old", help="Path to the old OpenAPI spec")
    parser.add_argument("new", help="Path to the new OpenAPI spec")
    parser.add_argument(
        "--format",
        choices=["text", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--breaking-only",
        action="store_true",
        help="Only show breaking changes",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with code 1 if breaking changes are found",
    )
    return parser


def run_discriminator(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    report = diff_discriminator(old_spec, new_spec)

    if args.breaking_only:
        report = filter_breaking_only(report)

    print(render(report, fmt=args.format))

    if args.fail_on_breaking and any(
        c.severity.value == "breaking" for c in report.changes
    ):
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="apidiff-discriminator")
    subparsers = parser.add_subparsers(dest="command")
    build_discriminator_parser(subparsers)
    args = parser.parse_args()
    sys.exit(run_discriminator(args))
