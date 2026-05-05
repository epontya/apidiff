"""CLI sub-command: tag — show diff changes grouped by OpenAPI tag."""

import argparse
import json
import sys

from apidiff.loader import load_spec, SpecLoadError
from apidiff.differ import diff_specs
from apidiff.tagger import tag_report


def build_tagger_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Show diff changes grouped by OpenAPI operation tag."
    if subparsers is not None:
        parser = subparsers.add_parser("tag", help=description)
    else:
        parser = argparse.ArgumentParser(prog="apidiff-tag", description=description)

    parser.add_argument("old", help="Path to the old OpenAPI spec")
    parser.add_argument("new", help="Path to the new OpenAPI spec")
    parser.add_argument(
        "--tag",
        dest="filter_tag",
        default=None,
        help="Only show changes for this tag",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return parser


def run_tagger(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_specs(old_spec, new_spec)
    tagged = tag_report(report, old_spec, new_spec)

    changes = (
        tagged.changes_for_tag(args.filter_tag)
        if args.filter_tag
        else tagged.tagged_changes
    )

    if args.format == "json":
        print(json.dumps([c.to_dict() for c in changes], indent=2))
        return 0

    if not changes:
        print("No changes found.")
        return 0

    current_tags = None
    for tc in changes:
        label = ", ".join(tc.tags) if tc.tags else "(untagged)"
        if label != current_tags:
            current_tags = label
            print(f"\n[{label}]")
        sev = tc.change.severity.value.upper()
        print(f"  [{sev}] {tc.change.path} ({tc.change.operation}) — {tc.change.description}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_tagger_parser()
    sys.exit(run_tagger(parser.parse_args()))
