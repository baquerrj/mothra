from __future__ import annotations

from datetime import date

from spending_visualizer.analysis.payment_matching import match_credit_card_payments
from spending_visualizer.config import AnalysisConfig
from spending_visualizer.domain.models import AccountType, OverrideDecision
from tests.support import build_account_descriptor, build_transaction


def test_match_credit_card_payments_scores_exact_amount_nearby_date_highly() -> None:
    checking_account = build_account_descriptor(
        account_type=AccountType.CHECKING,
        account_number="1234",
    )
    card_account = build_account_descriptor(
        account_type=AccountType.CREDITCARD,
        account_number="9876",
    )
    checking = (
        build_transaction(
            when=date(2026, 2, 10),
            amount="-200.00",
            description_raw="CITI CARD ONLINE PAYMENT",
            source_row=1,
            account=checking_account,
        ),
    )
    card_payments = (
        build_transaction(
            when=date(2026, 2, 11),
            amount="200.00",
            description_raw="ONLINE PAYMENT THANK YOU",
            source_row=1,
            account=card_account,
        ),
    )
    matches = match_credit_card_payments(checking, card_payments, {}, AnalysisConfig())
    assert len(matches) == 1
    assert matches[0].confidence >= 0.8


def test_match_credit_card_payments_enforces_one_to_one_pairing() -> None:
    checking_account = build_account_descriptor(
        account_type=AccountType.CHECKING,
        account_number="1234",
    )
    card_account = build_account_descriptor(
        account_type=AccountType.CREDITCARD,
        account_number="9876",
    )
    checking = (
        build_transaction(
            when=date(2026, 2, 10),
            amount="-200.00",
            description_raw="CITI CARD ONLINE PAYMENT",
            source_row=1,
            account=checking_account,
        ),
        build_transaction(
            when=date(2026, 2, 12),
            amount="-200.00",
            description_raw="CITI CARD ONLINE PAYMENT",
            source_row=2,
            account=checking_account,
        ),
    )
    card_payments = (
        build_transaction(
            when=date(2026, 2, 11),
            amount="200.00",
            description_raw="ONLINE PAYMENT THANK YOU",
            source_row=1,
            account=card_account,
        ),
    )
    matches = match_credit_card_payments(checking, card_payments, {}, AnalysisConfig())
    assert len(matches) == 1


def test_confirmed_payment_match_receives_status_and_confidence_boost() -> None:
    checking_account = build_account_descriptor(
        account_type=AccountType.CHECKING,
        account_number="1234",
    )
    card_account = build_account_descriptor(
        account_type=AccountType.CREDITCARD,
        account_number="9876",
    )
    checking_tx = build_transaction(
        when=date(2026, 2, 10),
        amount="-200.00",
        description_raw="CITI CARD ONLINE PAYMENT",
        source_row=1,
        account=checking_account,
    )
    card_tx = build_transaction(
        when=date(2026, 2, 11),
        amount="200.00",
        description_raw="ONLINE PAYMENT THANK YOU",
        source_row=1,
        account=card_account,
    )
    match_id = (
        f"{checking_account.storage_key}:1:"
        f"{card_account.storage_key}:1"
    )
    matches = match_credit_card_payments(
        (checking_tx,),
        (card_tx,),
        {match_id: OverrideDecision.CONFIRMED},
        AnalysisConfig(),
    )
    assert matches[0].status == OverrideDecision.CONFIRMED
    assert matches[0].confidence > 0.8
