from __future__ import annotations

from pathlib import Path

from spending_visualizer.application.services import (
    build_dashboard_bundle,
    build_payment_match_scope_key,
    build_report,
)
from spending_visualizer.domain.models import OverrideDecision
from spending_visualizer.ingest.csv_loader import load_transactions
from spending_visualizer.persistence.overrides import OverrideStore


def test_build_report_computes_recurring_totals(
    sample_csv_bytes: bytes,
    sample_checking_filename: str,
    tmp_path: Path,
) -> None:
    store = OverrideStore(tmp_path / "overrides.json")
    bundle = build_report(sample_csv_bytes, sample_checking_filename, store)
    assert bundle.recurring_expense_total > 0
    assert bundle.recurring_credit_total > 0


def test_build_report_returns_expense_breakdown_and_variable_totals(
    sample_csv_bytes: bytes,
    sample_checking_filename: str,
    tmp_path: Path,
) -> None:
    store = OverrideStore(tmp_path / "overrides.json")
    bundle = build_report(sample_csv_bytes, sample_checking_filename, store)
    assert bundle.fixed_recurring_expense_total > 0
    assert bundle.variable_recurring_expense_total > 0
    assert bundle.report.recurring_expense_breakdown
    assert bundle.report.variable_recurring_debits
    assert any(
        candidate.recurring_type.value == "variable"
        for candidate in bundle.report.variable_recurring_debits
    )


def test_build_dashboard_bundle_matches_credit_card_payments(
    sample_csv_bytes: bytes,
    sample_credit_card_csv_bytes: bytes,
    sample_checking_filename: str,
    sample_credit_card_filename: str,
    tmp_path: Path,
) -> None:
    store = OverrideStore(tmp_path / "overrides.json")
    checking = load_transactions(sample_csv_bytes, sample_checking_filename)
    credit_card = load_transactions(sample_credit_card_csv_bytes, sample_credit_card_filename)
    bundle = build_dashboard_bundle(checking, credit_card, store)
    assert bundle.report.cross_account_report is not None
    assert bundle.report.cross_account_report.payment_matches
    assert bundle.credit_card_bundle is not None
    assert bundle.credit_card_bundle.report.interest_transactions
    assert bundle.credit_card_bundle.report.interest_estimate is not None


def test_override_store_persists_only_local_metadata(tmp_path: Path) -> None:
    path = tmp_path / "overrides.json"
    store = OverrideStore(path)
    store.set_decision("scope-a", "candidate-1", OverrideDecision.CONFIRMED)
    store.set_payment_match_decision("scope-a__scope-b", "match-1", OverrideDecision.REJECTED)
    contents = path.read_text(encoding="utf-8")
    assert "candidate-1" in contents
    assert "match-1" in contents
    assert "Checking1.csv" not in contents


def test_override_store_is_keyed_by_scope(tmp_path: Path) -> None:
    store = OverrideStore(tmp_path / "overrides.json")
    store.set_decision("scope-a", "candidate-1", OverrideDecision.CONFIRMED)
    store.set_decision("scope-b", "candidate-1", OverrideDecision.REJECTED)
    assert store.get_decisions("scope-a")["candidate-1"] == OverrideDecision.CONFIRMED
    assert store.get_decisions("scope-b")["candidate-1"] == OverrideDecision.REJECTED


def test_build_report_is_deterministic_for_same_input(
    sample_csv_bytes: bytes,
    sample_checking_filename: str,
    tmp_path: Path,
) -> None:
    store = OverrideStore(tmp_path / "overrides.json")
    left = build_report(sample_csv_bytes, sample_checking_filename, store)
    right = build_report(sample_csv_bytes, sample_checking_filename, store)
    assert left.report == right.report


def test_payment_match_decisions_are_keyed_by_account_pair(
    sample_csv_bytes: bytes,
    sample_credit_card_csv_bytes: bytes,
    sample_checking_filename: str,
    sample_credit_card_filename: str,
    tmp_path: Path,
) -> None:
    store = OverrideStore(tmp_path / "overrides.json")
    checking = load_transactions(sample_csv_bytes, sample_checking_filename)
    credit_card = load_transactions(sample_credit_card_csv_bytes, sample_credit_card_filename)
    scope_key = build_payment_match_scope_key(
        checking.account.storage_key,
        credit_card.account.storage_key,
    )
    store.set_payment_match_decision(scope_key, "match-1", OverrideDecision.CONFIRMED)
    assert store.get_payment_match_decisions(scope_key)["match-1"] == OverrideDecision.CONFIRMED
