from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from spending_visualizer.analysis.recurring import detect_recurring_candidates
from spending_visualizer.config import AnalysisConfig
from spending_visualizer.domain.models import Direction, Transaction
from tests.support import build_transaction


def test_detects_monthly_recurring_debits(
    recurring_transactions: tuple[Transaction, ...],
) -> None:
    candidates = detect_recurring_candidates(
        recurring_transactions,
        Direction.DEBIT,
        AnalysisConfig(),
    )
    assert len(candidates) == 1
    assert candidates[0].cadence == "monthly"


def test_detects_biweekly_recurring_credits(
    recurring_transactions: tuple[Transaction, ...],
) -> None:
    candidates = detect_recurring_candidates(
        recurring_transactions,
        Direction.CREDIT,
        AnalysisConfig(),
    )
    assert len(candidates) == 1
    assert candidates[0].cadence == "biweekly"


def test_detects_weekly_recurring_items() -> None:
    transactions = tuple(
        build_transaction(
            when=date(2026, 1, 1) + timedelta(days=7 * idx),
            amount="-9.99",
            description_raw="Weekly Service",
            description_normalized="WEEKLY SERVICE",
            source_row=idx + 1,
        )
        for idx in range(4)
    )
    candidates = detect_recurring_candidates(transactions, Direction.DEBIT, AnalysisConfig())
    assert candidates[0].cadence == "weekly"


def test_estimated_monthly_amount_scales_by_cadence() -> None:
    transactions = tuple(
        build_transaction(
            when=date(2026, 1, 1) + timedelta(days=14 * idx),
            amount="-100.00",
            description_raw="Gym Membership",
            description_normalized="GYM MEMBERSHIP",
            source_row=idx + 1,
        )
        for idx in range(4)
    )
    candidates = detect_recurring_candidates(transactions, Direction.DEBIT, AnalysisConfig())
    assert candidates[0].estimated_monthly_amount == Decimal("216.67")


def test_recurring_candidates_include_confidence_and_evidence_fields() -> None:
    transactions = tuple(
        build_transaction(
            when=date(2026, 1, 1) + timedelta(days=30 * idx),
            amount="-50.00",
            description_raw="Insurance Payment",
            description_normalized="INSURANCE PAYMENT",
            source_row=idx + 1,
        )
        for idx in range(4)
    )
    candidate = detect_recurring_candidates(transactions, Direction.DEBIT, AnalysisConfig())[0]
    assert candidate.confidence >= 0.55
    assert candidate.expected_day_window.startswith("days")
