"""CLI command for detecting default value changes between two OpenAPI specs."""

import argparse
import json
import sys

from apidiff.differ_extensions_defaults import diff_defaults
from apidiff.formatter import render
from apidiff.loader import SpecLoadError, load_spec
from apidiff.summary import summarize, format_summary


def build_defaults_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Detect changes to default values in component schemas."
    if subparsers is not None:
        parser = subparsers.add_parser("defaults", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="apidiff-defaults", description=description)

    parser.add_argument("old", help="Path to the old OpenAPI spec (JSON or YAML)")
    parser.add_argument("new", help="Path to the new OpenAPI spec (JSON or YAML)")
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with code 1 if breaking changes are found",
    )
    return parser


def run_defaults(args) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_defaults(old_spec, new_spec)

    if args.format == "json":
        from apidiff.reporter import report_to_dict
        print(json.dumps(report_to_dict(report), indent=2))
    else:
        output = render(report, fmt=args.format)
        print(output)

    summary = summarize(report)
    print(format_summary(summary), file=sys.stderr)

    if args.fail_on_breaking and summary.breaking_count > 0:
        return 1
    return 0


def main():  # pragma: no cover
    parser = build_defaults_parser()
    args = parser.parse_args()
    sys.exit(run_defaults(args))


if __name__ == "__main__":  # pragma: no cover
    main()
