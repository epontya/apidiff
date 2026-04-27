"""CLI entry-point for the compatibility scorer."""

import argparse
import json
import sys

from apidiff.loader import load_spec, SpecLoadError
from apidiff.differ import build_diff
from apidiff.scorer import compute_score, format_score, score_to_dict


def build_scorer_parser(parent: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    parser = parent or argparse.ArgumentParser(
        prog="apidiff-score",
        description="Compute a compatibility score between two OpenAPI specs.",
    )
    parser.add_argument("old", help="Path to the old OpenAPI spec")
    parser.add_argument("new", help="Path to the new OpenAPI spec")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=80,
        metavar="N",
        help="Exit with code 1 when score is below N (default: 80)",
    )
    parser.add_argument(
        "--fail-below",
        action="store_true",
        help="Return exit code 1 if score is below --threshold",
    )
    return parser


def run_scorer(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = build_diff(old_spec, new_spec)
    cs = compute_score(report)

    if args.format == "json":
        print(json.dumps(score_to_dict(cs), indent=2))
    else:
        print(format_score(cs))

    if args.fail_below and not cs.is_passing(args.threshold):
        return 1
    return 0


def main() -> None:
    parser = build_scorer_parser()
    args = parser.parse_args()
    sys.exit(run_scorer(args))


if __name__ == "__main__":
    main()
