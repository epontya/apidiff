"""CLI entry point for the linter command."""

import argparse
import sys

from apidiff.loader import load_spec
from apidiff.differ import diff_specs
from apidiff.linter import lint_report


def build_linter_parser(parent: argparse.ArgumentParser = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(
        prog="apidiff-lint",
        description="Lint a diff report for quality issues.",
    )
    parser.add_argument("old", help="Path to the old OpenAPI spec")
    parser.add_argument("new", help="Path to the new OpenAPI spec")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code on warnings as well as errors.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def run_linter(args: argparse.Namespace) -> int:
    old_spec = load_spec(args.old)
    new_spec = load_spec(args.new)
    report = diff_specs(old_spec, new_spec)
    result = lint_report(report)

    if args.format == "json":
        import json
        issues = [{"code": i.code, "message": i.message, "severity": i.severity} for i in result.issues]
        print(json.dumps({"issues": issues, "has_errors": result.has_errors()}, indent=2))
    else:
        if not result.issues:
            print("No lint issues found.")
        for issue in result.issues:
            tag = issue.severity.upper()
            print(f"[{tag}] {issue.code}: {issue.message}")

    if result.has_errors():
        return 2
    if args.strict and result.has_warnings():
        return 1
    return 0


def main() -> None:
    parser = build_linter_parser()
    args = parser.parse_args()
    sys.exit(run_linter(args))


if __name__ == "__main__":
    main()
