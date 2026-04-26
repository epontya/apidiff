"""Tests for the gate module — policy-based pass/fail evaluation of diff reports."""

import pytest
from apidiff.gate import GateResult, run_gate
from apidiff.differ import Change, ChangeType, Severity, DiffReport


@pytest.fixture
def empty_report():
    return DiffReport(changes=[])


@pytest.fixture
def breaking_report():
    return DiffReport(
        changes=[
            Change(
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                path="/users",
                method="GET",
                description="Path removed",
            )
        ]
    )


@pytest.fixture
def non_breaking_report():
    return DiffReport(
        changes=[
            Change(
                change_type=ChangeType.ADDED,
                severity=Severity.NON_BREAKING,
                path="/items",
                method="POST",
                description="New endpoint added",
            )
        ]
    )


@pytest.fixture
def mixed_report():
    return DiffReport(
        changes=[
            Change(
                change_type=ChangeType.REMOVED,
                severity=Severity.BREAKING,
                path="/users",
                method="DELETE",
                description="Endpoint removed",
            ),
            Change(
                change_type=ChangeType.ADDED,
                severity=Severity.NON_BREAKING,
                path="/products",
                method="GET",
                description="New endpoint added",
            ),
        ]
    )


@pytest.fixture
def no_breaking_policy():
    return [{"rule": "no_breaking_changes"}]


@pytest.fixture
def empty_policy():
    return []


# --- GateResult bool behavior ---

def test_gate_result_passed_is_truthy():
    result = GateResult(passed=True, violations=[])
    assert bool(result) is True


def test_gate_result_failed_is_falsy():
    result = GateResult(passed=False, violations=["Breaking change detected"])
    assert bool(result) is False


# --- run_gate with empty policy ---

def test_empty_policy_always_passes(breaking_report, empty_policy):
    result = run_gate(breaking_report, empty_policy)
    assert result.passed is True
    assert result.violations == []


def test_empty_report_empty_policy_passes(empty_report, empty_policy):
    result = run_gate(empty_report, empty_policy)
    assert result.passed is True


# --- no_breaking_changes rule ---

def test_no_breaking_rule_passes_on_empty_report(empty_report, no_breaking_policy):
    result = run_gate(empty_report, no_breaking_policy)
    assert result.passed is True
    assert len(result.violations) == 0


def test_no_breaking_rule_passes_on_non_breaking_report(non_breaking_report, no_breaking_policy):
    result = run_gate(non_breaking_report, no_breaking_policy)
    assert result.passed is True


def test_no_breaking_rule_fails_on_breaking_report(breaking_report, no_breaking_policy):
    result = run_gate(breaking_report, no_breaking_policy)
    assert result.passed is False
    assert len(result.violations) > 0


def test_no_breaking_rule_fails_on_mixed_report(mixed_report, no_breaking_policy):
    result = run_gate(mixed_report, no_breaking_policy)
    assert result.passed is False


# --- summary method ---

def test_gate_result_summary_passed():
    result = GateResult(passed=True, violations=[])
    text = result.summary()
    assert "passed" in text.lower() or "pass" in text.lower()


def test_gate_result_summary_failed():
    result = GateResult(passed=False, violations=["Breaking change in /users GET"])
    text = result.summary()
    assert "fail" in text.lower() or "violation" in text.lower()


def test_gate_result_summary_includes_violation_text():
    violation_msg = "Breaking change in /users GET"
    result = GateResult(passed=False, violations=[violation_msg])
    text = result.summary()
    assert violation_msg in text
