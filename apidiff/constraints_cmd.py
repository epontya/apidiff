"""CLI sub-command: diff schema property constraints between two OpenAPI specs."""
import argparse
import sys

from apidiff.loader import load_spec, SpecLoadError
from apidiff.differ_extensions_constraints import diff_constraints
from apidiff.formatter import render
from apidiff.filters import filter_breaking_only


def build_constraints_parser(subparsers: argparse.ArgumentParser) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "constraints",
        help="Detect changes to schema property constraints (min/max, length, items, etc.).",
    )
    p.add_argument("old", help="Path to the old OpenAPI spec.")
    p.add_argument("new", help="Path to the new OpenAPI spec.")
    p.add_argument(
        "--format",
        choices=["text", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--breaking-only",
        action="store_true",
        help="Only show breaking constraint changes.",
    )
    p.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with code 1 if breaking changes are found.",
    )
    return p


def run_constraints(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_constraints(old_spec, new_spec)

    if args.breaking_only:
        report = filter_breaking_only(report)

    print(render(report, fmt=args.format))

    if args.fail_on_breaking and any(
        c.severity.value == "breaking" for c in report.changes
    ):
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="apidiff-constraints")
    subs = parser.add_subparsers(dest="command")
    build_constraints_parser(subs)
    args = parser.parse_args()
    sys.exit(run_constraints(args))


if __name__ == "__main__":
    main()
