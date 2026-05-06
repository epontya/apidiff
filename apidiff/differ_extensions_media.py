"""Detect breaking changes in media type definitions across OpenAPI specs."""

from __future__ import annotations

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_media_types(spec: dict, path: str, method: str, direction: str) -> dict:
    """Extract media type map from request body or response for a given path/method."""
    paths = spec.get("paths", {})
    operation = paths.get(path, {}).get(method, {})
    if direction == "request":
        return operation.get("requestBody", {}).get("content", {})
    if direction == "response":
        responses = operation.get("responses", {})
        media: dict = {}
        for status, resp in responses.items():
            for mt, mt_obj in resp.get("content", {}).items():
                media[f"{status}/{mt}"] = mt_obj
        return media
    return {}


def diff_media_types(old_spec: dict, new_spec: dict) -> DiffReport:
    """Compare media types between two OpenAPI specs and return a DiffReport."""
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")
    changes: list[Change] = []

    old_paths = old_spec.get("paths", {})
    new_paths = new_spec.get("paths", {})
    all_paths = set(old_paths) | set(new_paths)
    methods = ["get", "post", "put", "patch", "delete", "options", "head", "trace"]

    for path in all_paths:
        for method in methods:
            if method not in old_paths.get(path, {}) and method not in new_paths.get(path, {}):
                continue
            for direction in ("request", "response"):
                old_media = _get_media_types(old_spec, path, method, direction)
                new_media = _get_media_types(new_spec, path, method, direction)

                for mt in old_media:
                    if mt not in new_media:
                        changes.append(
                            Change(
                                change_type=ChangeType.REMOVED,
                                severity=Severity.BREAKING,
                                path=path,
                                operation=method.upper(),
                                description=(
                                    f"Media type '{mt}' removed from {direction} "
                                    f"of {method.upper()} {path}"
                                ),
                            )
                        )

                for mt in new_media:
                    if mt not in old_media:
                        changes.append(
                            Change(
                                change_type=ChangeType.ADDED,
                                severity=Severity.NON_BREAKING,
                                path=path,
                                operation=method.upper(),
                                description=(
                                    f"Media type '{mt}' added to {direction} "
                                    f"of {method.upper()} {path}"
                                ),
                            )
                        )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
