"""Detect breaking and non-breaking changes in response/request headers."""

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_headers(operation: dict) -> dict:
    """Extract headers from an operation's responses (first 2xx or first response)."""
    responses = operation.get("responses", {})
    for status, resp in responses.items():
        if str(status).startswith("2"):
            return resp.get("headers", {})
    # Fall back to first response
    for resp in responses.values():
        return resp.get("headers", {})
    return {}


def _header_required(header: dict) -> bool:
    return header.get("required", False)


def diff_headers(old_spec: dict, new_spec: dict) -> DiffReport:
    """Compare response headers across all paths and operations."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")
    changes: list[Change] = []

    old_paths = old_spec.get("paths", {})
    new_paths = new_spec.get("paths", {})

    for path, old_path_item in old_paths.items():
        new_path_item = new_paths.get(path, {})
        for method in ("get", "post", "put", "patch", "delete", "head", "options"):
            old_op = old_path_item.get(method)
            new_op = new_path_item.get(method)
            if not old_op:
                continue
            if not new_op:
                continue

            old_headers = _get_headers(old_op)
            new_headers = _get_headers(new_op)

            for header_name, old_header in old_headers.items():
                if header_name not in new_headers:
                    severity = (
                        Severity.BREAKING
                        if _header_required(old_header)
                        else Severity.NON_BREAKING
                    )
                    changes.append(
                        Change(
                            change_type=ChangeType.REMOVED,
                            severity=severity,
                            path=path,
                            operation=method.upper(),
                            description=f"Response header '{header_name}' removed",
                        )
                    )
                else:
                    new_header = new_headers[header_name]
                    old_schema = old_header.get("schema", {})
                    new_schema = new_header.get("schema", {})
                    if old_schema.get("type") != new_schema.get("type") and old_schema.get("type"):
                        changes.append(
                            Change(
                                change_type=ChangeType.MODIFIED,
                                severity=Severity.BREAKING,
                                path=path,
                                operation=method.upper(),
                                description=(
                                    f"Response header '{header_name}' type changed "
                                    f"from '{old_schema.get('type')}' to '{new_schema.get('type')}'"
                                ),
                            )
                        )

            for header_name, new_header in new_headers.items():
                if header_name not in old_headers:
                    changes.append(
                        Change(
                            change_type=ChangeType.ADDED,
                            severity=Severity.NON_BREAKING,
                            path=path,
                            operation=method.upper(),
                            description=f"Response header '{header_name}' added",
                        )
                    )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
