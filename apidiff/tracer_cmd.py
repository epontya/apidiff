"""CLI entry-point for the trace sub-command."""

from __future__ import annotations

import argparse
import sys

from apidiff.loader import load_spec, SpecLoadError
from apidiff.differ import diff_specs
from apidiff.tracer import trace_changes, format_trace


def build_tracer_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        description="Trace changes that affect a specific path pattern.",
    )
    if parent is not None:
        parser = parent.add_parser("trace", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="apidiff-trace", **kwargs)

    parser.add_argument("old", help="Path to the old OpenAPI spec")
    parser.add_argument("new", help="Path to the new OpenAPI spec")
    parser.add_argument("pattern", help="Glob pattern to match API paths (e.g. /users/*)")
    parser.add_argument(
        "--operation", "-op",
        default=None,
        help="Filter by HTTP operation (get, post, put, delete, …)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with code 1 if any matched change is breaking",
    )
    return parser


def run_tracer(args: argparse.Namespace) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    report = diff_specs(old_spec, new_spec)
    result = trace_changes(report, args.pattern, operation=args.operation)

    if args.format == "json":
        import json
        data = {
            "pattern": result.pattern,
            "old_version": result.old_version,
            "new_version": result.new_version,
            "matched": [
                {
                    "path": c.path,
                    "change_type": c.change_type.value,
                    "severity": c.severity.value,
                    "description": c.description,
                }
                for c in result.matched
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(format_trace(result))

    if args.fail_on_breaking and result.has_breaking():
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_tracer_parser()
    sys.exit(run_tracer(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
