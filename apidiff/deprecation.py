"""Detects deprecated endpoints and fields in OpenAPI specs."""

from dataclasses import dataclass, field
from typing import List, Optional

from apidiff.differ import Change, ChangeType, Severity, DiffReport


@dataclass
class DeprecationWarning_:
    path: str
    method: Optional[str]
    description: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "method": self.method,
            "description": self.description,
        }


@dataclass
class DeprecationReport:
    newly_deprecated: List[DeprecationWarning_] = field(default_factory=list)
    removed_deprecated: List[DeprecationWarning_] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.newly_deprecated and not self.removed_deprecated

    def to_dict(self) -> dict:
        return {
            "newly_deprecated": [w.to_dict() for w in self.newly_deprecated],
            "removed_deprecated": [w.to_dict() for w in self.removed_deprecated],
        }


def _get_operations(path_item: dict) -> List[str]:
    http_methods = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
    return [m for m in path_item if m.lower() in http_methods]


def detect_deprecations(old_spec: dict, new_spec: dict) -> DeprecationReport:
    """Compare two specs and return a report of deprecation changes."""
    report = DeprecationReport()

    old_paths = old_spec.get("paths", {})
    new_paths = new_spec.get("paths", {})

    for path, new_item in new_paths.items():
        old_item = old_paths.get(path, {})

        for method in _get_operations(new_item):
            new_op = new_item.get(method, {})
            old_op = old_item.get(method, {}) if old_item else {}

            was_deprecated = old_op.get("deprecated", False)
            is_deprecated = new_op.get("deprecated", False)

            if is_deprecated and not was_deprecated:
                report.newly_deprecated.append(
                    DeprecationWarning_(
                        path=path,
                        method=method.upper(),
                        description=f"{method.upper()} {path} is newly deprecated",
                    )
                )
            elif was_deprecated and not is_deprecated:
                report.removed_deprecated.append(
                    DeprecationWarning_(
                        path=path,
                        method=method.upper(),
                        description=f"{method.upper()} {path} deprecation was removed",
                    )
                )

    return report


def deprecation_report_to_changes(dep_report: DeprecationReport) -> List[Change]:
    """Convert a DeprecationReport into a list of Change objects for inclusion in DiffReport."""
    changes = []

    for warn in dep_report.newly_deprecated:
        changes.append(
            Change(
                change_type=ChangeType.DEPRECATED,
                severity=Severity.NON_BREAKING,
                path=warn.path,
                method=warn.method,
                description=warn.description,
            )
        )

    for warn in dep_report.removed_deprecated:
        changes.append(
            Change(
                change_type=ChangeType.MODIFIED,
                severity=Severity.NON_BREAKING,
                path=warn.path,
                method=warn.method,
                description=warn.description,
            )
        )

    return changes
