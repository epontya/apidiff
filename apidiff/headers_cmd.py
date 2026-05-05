"""CLI sub-command: apidiff headers — diff response headers between two specs."""

import argparse
import sys

from apidiff.differ_headers import diff_headers
from apidiff.formatter import render
from apidiff.loader import SpecLoadError, load_spec


def build_headers_parser(subparsers=None):
    description = "Detect header changes between two OpenAPI specs."
    if subparsers is not None:
        parser = subparsers.add_parser("headers", description=description)
    else:
        parser = argparse.ArgumentParser(description=description)

    parser.add_argument("old_spec", help="Path to the old OpenAPI spec")
    parser.add_argument("new_spec", help="Path to the new OpenAPI spec")
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        dest="format",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        default=False,
        help="Exit with code 1 if breaking header changes are found",
    )
    return parser


def run_headers(args) -> int:
    try:
        old_spec = load_spec(args.old_spec)
        new_spec = load_spec(args.new_spec)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_headers(old_spec, new_spec)
    output = render(report, fmt=args.format)
    print(output)

    if args.fail_on_breaking:
        from apidiff.differ import Severity
        breaking = [c for c in report.changes if c.severity == Severity.BREAKING]
        if breaking:
            return 1
    return 0


def main():
    parser = build_headers_parser()
    args = parser.parse_args()
    sys.exit(run_headers(args))


if __name__ == "__main__":
    main()
