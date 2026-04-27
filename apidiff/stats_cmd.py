"""CLI entry point for the `apidiff stats` sub-command."""

import argparse
import json
import sys

from apidiff.loader import load_spec, SpecLoadError
from apidiff.differ import diff_specs
from apidiff.stats import compute_stats, stats_to_dict, format_stats


def build_stats_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Show statistics about changes between two OpenAPI specs."
    if subparsers is not None:
        parser = subparsers.add_parser("stats", help=description)
    else:
        parser = argparse.ArgumentParser(prog="apidiff-stats", description=description)

    parser.add_argument("old", help="Path to the old OpenAPI spec (JSON or YAML).")
    parser.add_argument("new", help="Path to the new OpenAPI spec (JSON or YAML).")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        default=False,
        help="Exit with code 1 if any breaking changes are found.",
    )
    return parser


def run_stats(args: argparse.Namespace) -> int:
    """Execute the stats command. Returns an exit code."""
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_specs(old_spec, new_spec)
    stats = compute_stats(report)

    if args.format == "json":
        print(json.dumps(stats_to_dict(stats), indent=2))
    else:
        print(format_stats(stats))

    if args.fail_on_breaking and stats.breaking > 0:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_stats_parser()
    args = parser.parse_args()
    sys.exit(run_stats(args))


if __name__ == "__main__":  # pragma: no cover
    main()
