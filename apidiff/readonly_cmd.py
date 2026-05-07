"""CLI command for diffing readOnly/writeOnly flag changes."""

import argparse
import sys

from apidiff.loader import load_spec, SpecLoadError
from apidiff.differ_extensions_readonly import diff_readonly
from apidiff.formatter import render
from apidiff.filters import filter_breaking_only


def build_readonly_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Detect readOnly/writeOnly flag changes in component schemas."
    if subparsers is not None:
        parser = subparsers.add_parser("readonly", help=description)
    else:
        parser = argparse.ArgumentParser(prog="apidiff-readonly", description=description)

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


def run_readonly(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_readonly(
        old_spec,
        new_spec,
        old_version=old_spec.get("info", {}).get("version", "old"),
        new_version=new_spec.get("info", {}).get("version", "new"),
    )

    if args.breaking_only:
        report = filter_breaking_only(report)

    print(render(report, fmt=args.format))

    if args.fail_on_breaking and any(
        c.severity.value == "breaking" for c in report.changes
    ):
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_readonly_parser()
    args = parser.parse_args()
    sys.exit(run_readonly(args))


if __name__ == "__main__":  # pragma: no cover
    main()
