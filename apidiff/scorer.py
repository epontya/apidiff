"""Computes a compatibility score (0–100) for a diff report.

The score reflects how backward-compatible a change set is:
  100 = fully compatible (no changes or only non-breaking)
    0 = completely incompatible (many breaking changes)
"""

from dataclasses import dataclass
from apidiff.differ import DiffReport, Severity


# Penalty weights per severity
_SEVERITY_WEIGHT = {
    Severity.BREAKING: 10,
    Severity.WARNING: 3,
    Severity.INFO: 0,
}

_MAX_SCORE = 100


@dataclass
class CompatibilityScore:
    score: int          # 0–100
    total_changes: int
    penalty: int
    label: str          # EXCELLENT / GOOD / FAIR / POOR

    def is_passing(self, threshold: int = 80) -> bool:
        return self.score >= threshold


def _label_for_score(score: int) -> str:
    if score >= 90:
        return "EXCELLENT"
    if score >= 70:
        return "GOOD"
    if score >= 50:
        return "FAIR"
    return "POOR"


def compute_score(report: DiffReport) -> CompatibilityScore:
    """Return a CompatibilityScore derived from *report*."""
    penalty = 0
    for change in report.changes:
        penalty += _SEVERITY_WEIGHT.get(change.severity, 0)

    raw = _MAX_SCORE - penalty
    score = max(0, min(_MAX_SCORE, raw))
    return CompatibilityScore(
        score=score,
        total_changes=len(report.changes),
        penalty=penalty,
        label=_label_for_score(score),
    )


def format_score(cs: CompatibilityScore) -> str:
    """Return a human-readable summary of *cs*."""
    lines = [
        f"Compatibility Score : {cs.score}/100  [{cs.label}]",
        f"Total changes       : {cs.total_changes}",
        f"Total penalty       : {cs.penalty}",
    ]
    return "\n".join(lines)


def score_to_dict(cs: CompatibilityScore) -> dict:
    return {
        "score": cs.score,
        "label": cs.label,
        "total_changes": cs.total_changes,
        "penalty": cs.penalty,
    }
