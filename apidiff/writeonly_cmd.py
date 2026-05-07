"""CLI command for detecting writeOnly flag changes."""
import argparse
import sys
from typing import List, Optional

from apidiff.differ_extensions_writeonly import diff_writeonly
from apidiff.formatter import render
from apidiff.loader import SpecLoadError, load_spec


def build_writeonly_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Detect changes to writeOnly flags on schema properties."
    if subparsers is not None:
        parser = subparsers.add_parser("writeonly", help=description)
    else:
        parser = argparse.ArgumentParser(
            prog="apidiff-writeonly", description=description
        )
    parser.add_argument("old_spec", help="Path to the old OpenAPI spec.")
    parser.add_argument("new_spec", help="Path to the new OpenAPI spec.")
    parser.add_argument(
        "--format",
        choices=["text", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with code 1 if breaking changes are found.",
    )
    return parser


def run_writeonly(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old_spec)
        new_spec = load_spec(args.new_spec)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_writeonly(old_spec, new_spec)
    print(render(report, fmt=args.format))

    if args.fail_on_breaking and any(
        c.severity.value == "breaking" for c in report.changes
    ):
        return 1
    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_writeonly_parser()
    args = parser.parse_args(argv)
    sys.exit(run_writeonly(args))


if __name__ == "__main__":  # pragma: no cover
    main()
