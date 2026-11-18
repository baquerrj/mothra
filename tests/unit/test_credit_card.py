from __future__ import annotations

from datetime import date
from decimal import Decimal

from spending_visualizer.analysis.credit_card import (
    estimate_interest_rate,
    identify_credit_card_payments,
    identify_interest_transactions,
    identify_late_fee_transactions,
)
from spending_visualizer.config import AnalysisConfig
from spending_visualizer.domain.models import AccountType
from tests.support import build_account_descriptor, build_transaction


def test_credit_card_helpers_identify_payments_interest_and_fees() -> None:
    account = build_account_descriptor(account_type=AccountType.CREDITCARD, account_number="9876")
    transactions = (
        build_transaction(
            when=date(2026, 1, 3),
            amount="200.00",
            description_raw="ONLINE PAYMENT THANK YOU",
            source_row=1,
            account=account,
        ),
        build_transaction(
            when=date(2026, 1, 4),
            amount="-22.00",
            description_raw="INTEREST CHARGE ON PURCHASES",
            source_row=2,
            account=account,
        ),
        build_transaction(
            when=date(2026, 1, 5),
            amount="-35.00",
            description_raw="LATE FEE",
            source_row=3,
            account=account,
        ),
    )
    assert len(identify_credit_card_payments(transactions)) == 1
    assert len(identify_interest_transactions(transactions)) == 1
    assert len(identify_late_fee_transactions(transactions)) == 1


def test_estimate_interest_rate_returns_apr_and_trend() -> None:
    account = build_account_descriptor(
        account_type=AccountType.CREDITCARD,
        account_number="9876",
    )
    transactions = (
        build_transaction(
            when=date(2026, 1, 2),
            amount="-500.00",
            description_raw="PURCHASE A",
            source_row=1,
            account=account,
        ),
        build_transaction(
            when=date(2026, 1, 31),
            amount="-20.00",
            description_raw="INTEREST CHARGE ON PURCHASES",
            source_row=2,
            account=account,
        ),
        build_transaction(
            when=date(2026, 2, 5),
            amount="100.00",
            description_raw="ONLINE PAYMENT THANK YOU",
            source_row=3,
            account=account,
        ),
        build_transaction(
            when=date(2026, 2, 28),
            amount="-18.00",
            description_raw="INTEREST CHARGE ON PURCHASES",
            source_row=4,
            account=account,
        ),
        build_transaction(
            when=date(2026, 3, 1),
            amount="-50.00",
            description_raw="PURCHASE B",
            source_row=5,
            account=account,
        ),
        build_transaction(
            when=date(2026, 3, 31),
            amount="-19.00",
            description_raw="INTEREST CHARGE ON PURCHASES",
            source_row=6,
            account=account,
        ),
    )
    estimate = estimate_interest_rate(transactions, AnalysisConfig())
    assert estimate is not None
    assert estimate.current_apr is not None
    assert estimate.current_apr > Decimal("0.00")
    assert estimate.recent_average_apr is not None
    assert estimate.recent_interest_average > Decimal("0.00")
    assert "statement balances" in estimate.caveat
    assert (
        "trend" in estimate.trend_summary.lower()
        or "not enough" in estimate.trend_summary.lower()
    )
