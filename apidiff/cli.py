"""Command-line interface for apidiff."""

import argparse
import sys

from apidiff.loader import load_spec, SpecLoadError
from apidiff.differ import diff_specs
from apidiff.reporter import report_to_text, report_to_json, write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apidiff",
        description="Detect breaking changes between two OpenAPI spec versions.",
    )
    parser.add_argument("base", help="Path to the base (old) OpenAPI spec file.")
    parser.add_argument("revision", help="Path to the revised (new) OpenAPI spec file.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write report to FILE instead of stdout.",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        default=False,
        help="Exit with code 1 if breaking changes are detected.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        base_spec = load_spec(args.base)
        revision_spec = load_spec(args.revision)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_specs(base_spec, revision_spec)

    if args.format == "json":
        output = report_to_json(report)
    else:
        output = report_to_text(report)

    if args.output:
        write_report(output, args.output)
    else:
        print(output)

    if args.fail_on_breaking and report.has_breaking_changes():
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
