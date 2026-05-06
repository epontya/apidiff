"""Diff server definitions between two OpenAPI specs."""

from typing import Any

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_servers(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a mapping of server URL -> server object."""
    servers = spec.get("servers", [])
    return {s["url"]: s for s in servers if "url" in s}


def diff_servers(old_spec: dict[str, Any], new_spec: dict[str, Any]) -> DiffReport:
    """Compare server lists between old and new specs.

    Removing a server URL is breaking (clients may rely on it).
    Adding a server URL is non-breaking.
    Changing a server description is non-breaking.
    """
    old_version = old_spec.get("info", {}).get("version", "unknown")
    new_version = new_spec.get("info", {}).get("version", "unknown")

    old_servers = _get_servers(old_spec)
    new_servers = _get_servers(new_spec)

    changes: list[Change] = []

    # Detect removed servers (breaking)
    for url in old_servers:
        if url not in new_servers:
            changes.append(
                Change(
                    change_type=ChangeType.REMOVED,
                    severity=Severity.BREAKING,
                    path=f"servers[{url}]",
                    operation=None,
                    description=f"Server '{url}' was removed.",
                )
            )

    # Detect added servers (non-breaking)
    for url in new_servers:
        if url not in old_servers:
            changes.append(
                Change(
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    path=f"servers[{url}]",
                    operation=None,
                    description=f"Server '{url}' was added.",
                )
            )

    # Detect description changes (non-breaking)
    for url in old_servers:
        if url in new_servers:
            old_desc = old_servers[url].get("description", "")
            new_desc = new_servers[url].get("description", "")
            if old_desc != new_desc:
                changes.append(
                    Change(
                        change_type=ChangeType.MODIFIED,
                        severity=Severity.NON_BREAKING,
                        path=f"servers[{url}].description",
                        operation=None,
                        description=(
                            f"Server '{url}' description changed "
                            f"from '{old_desc}' to '{new_desc}'."
                        ),
                    )
                )

    return DiffReport(
        old_version=old_version,
        new_version=new_version,
        changes=changes,
    )
