"""CLI helper for generating changelog output from a diff."""

import argparse
import sys
from apidiff.loader import load_spec, SpecLoadError
from apidiff.differ import breaking_changes
from apidiff.changelog import build_changelog_entry, format_changelog, write_changelog


def build_changelog_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Generate a changelog entry from two OpenAPI specs."
    if subparsers is not None:
        parser = subparsers.add_parser("changelog", help=description)
    else:
        parser = argparse.ArgumentParser(prog="apidiff-changelog", description=description)

    parser.add_argument("old_spec", help="Path to the old OpenAPI spec file")
    parser.add_argument("new_spec", help="Path to the new OpenAPI spec file")
    parser.add_argument(
        "--version", default="Unreleased", help="Version label for the changelog entry"
    )
    parser.add_argument(
        "--output", "-o", default=None, help="Write changelog to this file instead of stdout"
    )
    parser.add_argument(
        "--breaking-only",
        action="store_true",
        default=False,
        help="Only include breaking changes in the changelog",
    )
    return parser


def run_changelog(args) -> int:
    """Execute the changelog command. Returns exit code."""
    try:
        old = load_spec(args.old_spec)
        new = load_spec(args.new_spec)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 1

    report = breaking_changes(old, new)
    entry = build_changelog_entry(report, version=args.version)
    include_non_breaking = not args.breaking_only

    if args.output:
        write_changelog(entry, args.output, include_non_breaking=include_non_breaking)
        print(f"Changelog written to {args.output}")
    else:
        print(format_changelog(entry, include_non_breaking=include_non_breaking))

    return 0


def main() -> None:  # pragma: no cover
    parser = build_changelog_parser()
    args = parser.parse_args()
    sys.exit(run_changelog(args))


if __name__ == "__main__":  # pragma: no cover
    main()
