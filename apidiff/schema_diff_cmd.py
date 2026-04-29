"""CLI command for comparing schemas between two OpenAPI specs."""

import argparse
import json
import sys

from apidiff.loader import load_spec, SpecLoadError
from apidiff.comparator import compare_schemas
from apidiff.differ import ChangeType, Severity


def build_schema_diff_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Compare schemas at a specific path between two OpenAPI specs."
    if subparsers:
        parser = subparsers.add_parser("schema-diff", help=description)
    else:
        parser = argparse.ArgumentParser(prog="apidiff schema-diff", description=description)

    parser.add_argument("old", help="Path to the old OpenAPI spec file")
    parser.add_argument("new", help="Path to the new OpenAPI spec file")
    parser.add_argument("--api-path", required=True, help="API path to compare (e.g. /users)")
    parser.add_argument("--method", default="post", help="HTTP method (default: post)")
    parser.add_argument("--schema-ref", default="requestBody", choices=["requestBody", "response"],
                        help="Which schema to compare (default: requestBody)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def _extract_schema(spec: dict, api_path: str, method: str, schema_ref: str) -> dict:
    try:
        op = spec["paths"][api_path][method.lower()]
        if schema_ref == "requestBody":
            return op["requestBody"]["content"]["application/json"]["schema"]
        else:
            return op["responses"]["200"]["content"]["application/json"]["schema"]
    except KeyError:
        return {}


def run_schema_diff(args) -> int:
    try:
        old_spec = load_spec(args.old)
        new_spec = load_spec(args.new)
    except SpecLoadError as e:
        print(f"Error loading spec: {e}", file=sys.stderr)
        return 2

    old_schema = _extract_schema(old_spec, args.api_path, args.method, args.schema_ref)
    new_schema = _extract_schema(new_spec, args.api_path, args.method, args.schema_ref)

    diffs = compare_schemas(args.api_path, old_schema, new_schema)

    if args.format == "json":
        output = [
            {
                "field": d.field_name,
                "change_type": d.change_type.value,
                "severity": d.severity.value,
                "old_value": d.old_value,
                "new_value": d.new_value,
            }
            for d in diffs
        ]
        print(json.dumps(output, indent=2))
    else:
        if not diffs:
            print("No schema differences found.")
        for d in diffs:
            tag = "[BREAKING]" if d.severity == Severity.BREAKING else "[non-breaking]"
            print(f"{tag} {d.change_type.value}: {d.field_name}")

    has_breaking = any(d.severity == Severity.BREAKING for d in diffs)
    return 1 if has_breaking else 0


def main():
    parser = build_schema_diff_parser()
    args = parser.parse_args()
    sys.exit(run_schema_diff(args))


if __name__ == "__main__":
    main()
