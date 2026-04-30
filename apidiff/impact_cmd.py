"""CLI command for generating an impact report from a diff."""

import argparse
import json
import sys

from apidiff.loader import load_spec, SpecLoadError
from apidiff.differ import diff_specs
from apidiff.impact import build_impact_report, format_impact_report, impact_to_dict


def build_impact_parser(subparsers=None):
    description = "Show which API paths and operations are impacted by breaking changes."
    if subparsers is not None:
        parser = subparsers.add_parser("impact", help=description)
    else:
        parser = argparse.ArgumentParser(prog="apidiff-impact", description=description)

    parser.add_argument("old", help="Path to the old OpenAPI spec")
    parser.add_argument("new", help="Path to the new OpenAPI spec")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-impact",
        action="store_true",
        help="Exit with code 1 if any impacted areas are found",
    )
    return parser


def run_impact(args) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_specs(old_spec, new_spec)
    impact = build_impact_report(report)

    if args.format == "json":
        print(json.dumps(impact_to_dict(impact), indent=2))
    else:
        print(format_impact_report(impact))

    if args.fail_on_impact and not impact.is_empty():
        return 1
    return 0


def main():
    parser = build_impact_parser()
    args = parser.parse_args()
    sys.exit(run_impact(args))


if __name__ == "__main__":
    main()
