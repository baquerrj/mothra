from __future__ import annotations

from pathlib import Path

from spending_visualizer.application.services import build_report
from spending_visualizer.domain.models import OverrideDecision
from spending_visualizer.persistence.overrides import OverrideStore


def test_build_report_computes_recurring_totals(
    sample_csv_bytes: bytes,
    tmp_path: Path,
) -> None:
    store = OverrideStore(tmp_path / "overrides.json")
    bundle = build_report(sample_csv_bytes, store)
    assert bundle.recurring_expense_total > 0
    assert bundle.recurring_credit_total > 0


def test_build_report_returns_expense_breakdown_and_variable_totals(
    sample_csv_bytes: bytes,
    tmp_path: Path,
) -> None:
    store = OverrideStore(tmp_path / "overrides.json")
    bundle = build_report(sample_csv_bytes, store)
    assert bundle.fixed_recurring_expense_total > 0
    assert bundle.variable_recurring_expense_total > 0
    assert bundle.report.recurring_expense_breakdown
    assert bundle.report.variable_recurring_debits
    assert any(
        candidate.recurring_type.value == "variable"
        for candidate in bundle.report.variable_recurring_debits
    )


def test_override_store_persists_only_local_metadata(tmp_path: Path) -> None:
    path = tmp_path / "overrides.json"
    store = OverrideStore(path)
    store.set_decision("file-a", "candidate-1", OverrideDecision.CONFIRMED)
    contents = path.read_text(encoding="utf-8")
    assert "candidate-1" in contents
    assert "Checking1.csv" not in contents


def test_override_store_is_keyed_by_fingerprint(tmp_path: Path) -> None:
    store = OverrideStore(tmp_path / "overrides.json")
    store.set_decision("file-a", "candidate-1", OverrideDecision.CONFIRMED)
    store.set_decision("file-b", "candidate-1", OverrideDecision.REJECTED)
    assert store.get_decisions("file-a")["candidate-1"] == OverrideDecision.CONFIRMED
    assert store.get_decisions("file-b")["candidate-1"] == OverrideDecision.REJECTED


def test_build_report_is_deterministic_for_same_input(
    sample_csv_bytes: bytes,
    tmp_path: Path,
) -> None:
    store = OverrideStore(tmp_path / "overrides.json")
    left = build_report(sample_csv_bytes, store)
    right = build_report(sample_csv_bytes, store)
    assert left.report == right.report
