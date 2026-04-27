"""CLI entry-point for the annotation / migration-guide sub-command."""

import argparse
import sys

from apidiff.annotator import annotate_report
from apidiff.annotation_formatter import render_annotated
from apidiff.differ import diff_specs
from apidiff.loader import load_spec, SpecLoadError


def build_annotation_parser(parent: argparse.ArgumentParser = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(
        prog="apidiff annotate",
        description="Generate a migration guide between two OpenAPI specs.",
    )
    parser.add_argument("old", help="Path to the old OpenAPI spec")
    parser.add_argument("new", help="Path to the new OpenAPI spec")
    parser.add_argument(
        "--format",
        choices=["text", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Write output to this file instead of stdout",
    )
    return parser


def run_annotation(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_specs(old_spec, new_spec)
    annotated = annotate_report(report)
    rendered = render_annotated(annotated, fmt=args.format)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(rendered)
    else:
        print(rendered)

    return 0


def main(argv=None) -> int:
    parser = build_annotation_parser()
    args = parser.parse_args(argv)
    return run_annotation(args)


if __name__ == "__main__":
    sys.exit(main())
