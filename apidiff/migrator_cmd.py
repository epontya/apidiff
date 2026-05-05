"""CLI entry-point for the migration-plan sub-command."""

import argparse
import json
import sys

from apidiff.loader import SpecLoadError, load_spec
from apidiff.differ import diff_specs
from apidiff.migrator import build_migration_plan, format_migration_plan


def build_migrator_parser(parent: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(
        prog="apidiff-migrate",
        description="Generate a migration plan for breaking API changes.",
    )
    parser.add_argument("old_spec", help="Path to the old OpenAPI spec (JSON or YAML).")
    parser.add_argument("new_spec", help="Path to the new OpenAPI spec (JSON or YAML).")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Write output to FILE instead of stdout.",
    )
    return parser


def run_migrator(args: argparse.Namespace) -> int:
    try:
        old = load_spec(args.old_spec)
        new = load_spec(args.new_spec)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_specs(old, new)
    plan = build_migration_plan(report)

    if args.format == "json":
        rendered = json.dumps(plan.to_dict(), indent=2)
    else:
        rendered = format_migration_plan(plan)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(rendered + "\n")
        except OSError as exc:
            print(f"Error writing output: {exc}", file=sys.stderr)
            return 2
    else:
        print(rendered)

    return 1 if (not plan.is_empty()) else 0


def main() -> None:  # pragma: no cover
    parser = build_migrator_parser()
    sys.exit(run_migrator(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
