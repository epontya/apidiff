"""CLI command for diffing webhook definitions between two OpenAPI specs."""
from __future__ import annotations

import argparse
import sys

from apidiff.loader import load_spec, SpecLoadError
from apidiff.differ_webhooks import diff_webhooks
from apidiff.formatter import render
from apidiff.filters import filter_breaking_only


def build_webhooks_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    kwargs: dict = dict(
        description="Diff webhook definitions between two OpenAPI specs.",
    )
    if parent is not None:
        parser = parent.add_parser("webhooks", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("old", help="Path to the old OpenAPI spec.")
    parser.add_argument("new", help="Path to the new OpenAPI spec.")
    parser.add_argument(
        "--format",
        choices=["text", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--breaking-only",
        action="store_true",
        help="Only show breaking changes.",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with code 1 if breaking changes are found.",
    )
    return parser


def run_webhooks(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_webhooks(old_spec, new_spec)

    if args.breaking_only:
        report = filter_breaking_only(report)

    print(render(report, fmt=args.format))

    if args.fail_on_breaking and any(
        c.severity.value == "breaking" for c in report.changes
    ):
        return 1
    return 0


def main() -> None:
    parser = build_webhooks_parser()
    args = parser.parse_args()
    sys.exit(run_webhooks(args))


if __name__ == "__main__":
    main()
