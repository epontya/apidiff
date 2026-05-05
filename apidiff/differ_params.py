"""Detect breaking changes in query/path/header parameters between two OpenAPI specs."""

from apidiff.differ import Change, ChangeType, DiffReport, Severity


def _get_parameters(spec: dict, path: str, method: str) -> dict:
    """Return a dict of {(name, in): param} for a given operation."""
    path_item = spec.get("paths", {}).get(path, {})
    operation = path_item.get(method, {})
    params = {}
    for p in operation.get("parameters", []):
        key = (p.get("name"), p.get("in"))
        params[key] = p
    return params


def _param_type(param: dict) -> str | None:
    schema = param.get("schema", {})
    return schema.get("type")


def diff_parameters(old_spec: dict, new_spec: dict) -> DiffReport:
    """Compare parameters across all shared operations and return a DiffReport."""
    old_ver = old_spec.get("info", {}).get("version", "unknown")
    new_ver = new_spec.get("info", {}).get("version", "unknown")
    changes: list[Change] = []

    old_paths = old_spec.get("paths", {})
    new_paths = new_spec.get("paths", {})

    for path, path_item in old_paths.items():
        if path not in new_paths:
            continue
        for method in ("get", "post", "put", "patch", "delete", "head", "options"):
            if method not in path_item:
                continue
            if method not in new_paths[path]:
                continue

            old_params = _get_parameters(old_spec, path, method)
            new_params = _get_parameters(new_spec, path, method)

            # Removed parameters
            for key, old_p in old_params.items():
                if key not in new_params:
                    required = old_p.get("required", False)
                    severity = Severity.BREAKING if required else Severity.NON_BREAKING
                    changes.append(
                        Change(
                            change_type=ChangeType.REMOVED,
                            severity=severity,
                            path=path,
                            operation=method.upper(),
                            description=(
                                f"Parameter '{key[0]}' (in {key[1]}) removed"
                            ),
                        )
                    )

            # Added parameters
            for key, new_p in new_params.items():
                if key not in old_params:
                    required = new_p.get("required", False)
                    severity = Severity.BREAKING if required else Severity.NON_BREAKING
                    changes.append(
                        Change(
                            change_type=ChangeType.ADDED,
                            severity=severity,
                            path=path,
                            operation=method.upper(),
                            description=(
                                f"Parameter '{key[0]}' (in {key[1]}) added"
                            ),
                        )
                    )

            # Modified parameters
            for key in old_params:
                if key not in new_params:
                    continue
                old_type = _param_type(old_params[key])
                new_type = _param_type(new_params[key])
                if old_type != new_type:
                    changes.append(
                        Change(
                            change_type=ChangeType.MODIFIED,
                            severity=Severity.BREAKING,
                            path=path,
                            operation=method.upper(),
                            description=(
                                f"Parameter '{key[0]}' (in {key[1]}) type changed "
                                f"from '{old_type}' to '{new_type}'"
                            ),
                        )
                    )

    return DiffReport(
        old_version=old_ver,
        new_version=new_ver,
        changes=changes,
    )
