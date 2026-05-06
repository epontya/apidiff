"""CLI command for detecting deprecated operation changes."""

import argparse
import sys

from apidiff.differ_extensions_deprecated import diff_deprecated_operations
from apidiff.formatter import render
from apidiff.loader import SpecLoadError, load_spec


def build_deprecated_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Detect operations that became deprecated or had deprecation removed."
    if subparsers:
        parser = subparsers.add_parser("deprecated", description=description)
    else:
        parser = argparse.ArgumentParser(prog="apidiff-deprecated", description=description)

    parser.add_argument("old", help="Path to the old OpenAPI spec")
    parser.add_argument("new", help="Path to the new OpenAPI spec")
    parser.add_argument(
        "--format",
        choices=["text", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-changes",
        action="store_true",
        help="Exit with code 1 if any deprecation changes are detected",
    )
    return parser


def run_deprecated(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_deprecated_operations(old_spec, new_spec)
    print(render(report, fmt=args.format))

    if args.fail_on_changes and report.changes:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_deprecated_parser()
    args = parser.parse_args()
    sys.exit(run_deprecated(args))


if __name__ == "__main__":  # pragma: no cover
    main()
