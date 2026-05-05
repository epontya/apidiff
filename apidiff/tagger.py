"""Tag changes in a DiffReport based on OpenAPI operation tags."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from apidiff.differ import Change, DiffReport


@dataclass
class TaggedChange:
    change: Change
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tags": self.tags,
            "path": self.change.path,
            "operation": self.change.operation,
            "change_type": self.change.change_type.value,
            "severity": self.change.severity.value,
            "description": self.change.description,
        }


@dataclass
class TaggedReport:
    old_version: str
    new_version: str
    tagged_changes: List[TaggedChange] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.tagged_changes) == 0

    def changes_for_tag(self, tag: str) -> List[TaggedChange]:
        return [tc for tc in self.tagged_changes if tag in tc.tags]

    def all_tags(self) -> List[str]:
        tags: List[str] = []
        for tc in self.tagged_changes:
            for t in tc.tags:
                if t not in tags:
                    tags.append(t)
        return sorted(tags)


def _extract_tags(spec: dict, path: str, operation: Optional[str]) -> List[str]:
    """Resolve tags from the spec for a given path and operation."""
    if not operation:
        return []
    try:
        op_obj = spec.get("paths", {}).get(path, {}).get(operation.lower(), {})
        return list(op_obj.get("tags", []))
    except (AttributeError, TypeError):
        return []


def tag_report(
    report: DiffReport,
    old_spec: dict,
    new_spec: dict,
) -> TaggedReport:
    """Annotate each change in *report* with the tags from the OpenAPI specs.

    Tags are sourced from *new_spec* first; if the operation no longer exists
    (e.g. removed path) the tags are taken from *old_spec*.
    """
    tagged: List[TaggedChange] = []
    for change in report.changes:
        tags = _extract_tags(new_spec, change.path, change.operation)
        if not tags:
            tags = _extract_tags(old_spec, change.path, change.operation)
        tagged.append(TaggedChange(change=change, tags=tags))

    return TaggedReport(
        old_version=report.old_version,
        new_version=report.new_version,
        tagged_changes=tagged,
    )
