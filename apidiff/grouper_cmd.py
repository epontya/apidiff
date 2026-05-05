"""CLI command for grouping a diff report by severity, path prefix, or change type."""

from __future__ import annotations

import argparse
import json
import sys

from apidiff.loader import load_spec, SpecLoadError
from apidiff.differ import build_report
from apidiff.grouper import (
    group_by_severity,
    group_by_path_prefix,
    group_by_change_type,
    grouped_report_to_dict,
)

_STRATEGIES = {
    "severity": group_by_severity,
    "change_type": group_by_change_type,
}


def build_grouper_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    kwargs = dict(
        description="Group diff changes by a chosen dimension.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser = parent.add_parser("group", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("old", help="Path to the old OpenAPI spec")
    parser.add_argument("new", help="Path to the new OpenAPI spec")
    parser.add_argument(
        "--by",
        choices=["severity", "change_type", "path"],
        default="severity",
        help="Dimension to group by (default: severity)",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Path prefix depth when grouping by path (default: 1)",
    )
    return parser


def run_grouper(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = build_report(old_spec, new_spec)

    if args.by == "path":
        grouped = group_by_path_prefix(report, depth=args.depth)
    else:
        grouped = _STRATEGIES[args.by](report)

    data = grouped_report_to_dict(grouped)
    print(json.dumps(data, indent=2))
    return 0


def main() -> None:
    parser = build_grouper_parser()
    args = parser.parse_args()
    sys.exit(run_grouper(args))


if __name__ == "__main__":
    main()
