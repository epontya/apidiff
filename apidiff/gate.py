"""Quality gate: combine validation + policy to produce a pass/fail exit signal."""

from dataclasses import dataclass
from typing import List, Optional

from apidiff.differ import DiffReport
from apidiff.policy import load_policy
from apidiff.validator import (
    ValidationResult,
    ValidationRule,
    default_strict_rules,
    validate_report,
)


@dataclass
class GateResult:
    """Outcome of a quality gate check."""
    passed: bool
    validation_result: ValidationResult

    def __bool__(self) -> bool:
        return self.passed

    def summary(self) -> str:
        if self.passed:
            return "Quality gate PASSED — no policy violations found."
        lines = ["Quality gate FAILED — violations:"]
        for v in self.validation_result.violations:
            lines.append(f"  • {v}")
        return "\n".join(lines)


def run_gate(
    report: DiffReport,
    policy_path: Optional[str] = None,
    strict: bool = False,
) -> GateResult:
    """Run the quality gate against a diff report.

    Args:
        report: The diff report to validate.
        policy_path: Optional path to a YAML/JSON policy file.
        strict: If True and no policy_path given, use default strict rules.

    Returns:
        A GateResult indicating pass/fail and any violations.
    """
    rules: List[ValidationRule]

    if policy_path:
        rules = load_policy(policy_path)
    elif strict:
        rules = default_strict_rules()
    else:
        rules = []

    validation_result = validate_report(report, rules)
    return GateResult(passed=validation_result.passed, validation_result=validation_result)
