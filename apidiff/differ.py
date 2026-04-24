"""Core diffing logic for comparing two OpenAPI specs."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class Severity(str, Enum):
    BREAKING = "breaking"
    NON_BREAKING = "non-breaking"
    INFO = "info"


@dataclass
class Change:
    path: str
    change_type: ChangeType
    severity: Severity
    old_value: Any = None
    new_value: Any = None
    description: str = ""


@dataclass
class DiffReport:
    changes: list[Change] = field(default_factory=list)

    @property
    def breaking_changes(self) -> list[Change]:
        return [c for c in self.changes if c.severity == Severity.BREAKING]

    @property
    def has_breaking_changes(self) -> bool:
        return len(self.breaking_changes) > 0

    def summary(self) -> dict:
        return {
            "total": len(self.changes),
            "breaking": len(self.breaking_changes),
            "non_breaking": sum(
                1 for c in self.changes if c.severity == Severity.NON_BREAKING
            ),
            "info": sum(1 for c in self.changes if c.severity == Severity.INFO),
        }


def diff_specs(old_spec: dict, new_spec: dict) -> DiffReport:
    """Compare two OpenAPI specs and return a structured DiffReport."""
    report = DiffReport()
    _diff_paths(old_spec.get("paths", {}), new_spec.get("paths", {}), report)
    _diff_info(old_spec.get("info", {}), new_spec.get("info", {}), report)
    return report


def _diff_info(old_info: dict, new_info: dict, report: DiffReport) -> None:
    old_version = old_info.get("version")
    new_version = new_info.get("version")
    if old_version != new_version:
        report.changes.append(
            Change(
                path="info.version",
                change_type=ChangeType.MODIFIED,
                severity=Severity.INFO,
                old_value=old_version,
                new_value=new_version,
                description="API version changed",
            )
        )


def _diff_paths(old_paths: dict, new_paths: dict, report: DiffReport) -> None:
    for path, old_item in old_paths.items():
        if path not in new_paths:
            report.changes.append(
                Change(
                    path=f"paths.{path}",
                    change_type=ChangeType.REMOVED,
                    severity=Severity.BREAKING,
                    old_value=path,
                    description=f"Path '{path}' was removed",
                )
            )
        else:
            _diff_path_item(path, old_item, new_paths[path], report)

    for path in new_paths:
        if path not in old_paths:
            report.changes.append(
                Change(
                    path=f"paths.{path}",
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    new_value=path,
                    description=f"Path '{path}' was added",
                )
            )


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


def _diff_path_item(
    path: str, old_item: dict, new_item: dict, report: DiffReport
) -> None:
    for method in HTTP_METHODS:
        old_op = old_item.get(method)
        new_op = new_item.get(method)
        if old_op and not new_op:
            report.changes.append(
                Change(
                    path=f"paths.{path}.{method}",
                    change_type=ChangeType.REMOVED,
                    severity=Severity.BREAKING,
                    description=f"Operation {method.upper()} '{path}' was removed",
                )
            )
        elif not old_op and new_op:
            report.changes.append(
                Change(
                    path=f"paths.{path}.{method}",
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    description=f"Operation {method.upper()} '{path}' was added",
                )
            )
        elif old_op and new_op:
            _diff_operation(path, method, old_op, new_op, report)


def _diff_operation(
    path: str, method: str, old_op: dict, new_op: dict, report: DiffReport
) -> None:
    old_params = {p["name"]: p for p in old_op.get("parameters", []) if "name" in p}
    new_params = {p["name"]: p for p in new_op.get("parameters", []) if "name" in p}

    for name, param in old_params.items():
        if name not in new_params:
            report.changes.append(
                Change(
                    path=f"paths.{path}.{method}.parameters.{name}",
                    change_type=ChangeType.REMOVED,
                    severity=Severity.BREAKING,
                    description=f"Parameter '{name}' removed from {method.upper()} '{path}'",
                )
            )
        else:
            new_param = new_params[name]
            if param.get("required") is False and new_param.get("required") is True:
                report.changes.append(
                    Change(
                        path=f"paths.{path}.{method}.parameters.{name}.required",
                        change_type=ChangeType.MODIFIED,
                        severity=Severity.BREAKING,
                        old_value=False,
                        new_value=True,
                        description=f"Parameter '{name}' became required in {method.upper()} '{path}'",
                    )
                )

    for name in new_params:
        if name not in old_params:
            report.changes.append(
                Change(
                    path=f"paths.{path}.{method}.parameters.{name}",
                    change_type=ChangeType.ADDED,
                    severity=Severity.NON_BREAKING,
                    description=f"Parameter '{name}' added to {method.upper()} '{path}'",
                )
            )
