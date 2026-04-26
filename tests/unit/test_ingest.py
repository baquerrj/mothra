from __future__ import annotations

from decimal import Decimal

import pytest

from spending_visualizer.ingest.csv_loader import (
    IngestionError,
    load_transactions,
    normalize_description,
)


def test_load_transactions_supports_headered_csv() -> None:
    csv_bytes = (
        b"Date,Amount,Description,Ignored\n"
        b"2026-04-01,-10.50,Music Subscription,foo\n"
        b"2026-04-02,1200.00,Payroll,bar\n"
    )
    parsed = load_transactions(csv_bytes)
    assert len(parsed.transactions) == 2
    assert parsed.transactions[0].description_normalized == "MUSIC SUBSCRIPTION"


def test_load_transactions_supports_wells_fargo_style_csv() -> None:
    csv_bytes = (
        b'"04/24/2026","-20.00","*","","RECURRING PAYMENT AUTHORIZED ON 04/21 '
        b'CLAUDE AI SUBSCRIPTION CARD 1234"\n'
    )
    parsed = load_transactions(csv_bytes)
    assert parsed.transactions[0].description_normalized == "CLAUDE AI SUBSCRIPTION"


def test_transaction_normalization_uses_decimal_and_source_rows() -> None:
    csv_bytes = b"Date,Amount,Description\n2026-04-01,-10.50,Music Subscription\n"
    parsed = load_transactions(csv_bytes)
    transaction = parsed.transactions[0]
    assert transaction.amount == Decimal("-10.50")
    assert transaction.source_row == 2


def test_normalize_description_removes_card_noise() -> None:
    normalized = normalize_description(
        "PURCHASE AUTHORIZED ON 04/22 KING SOOPERS #0132 CASTLE ROCK CO S356112860254084 CARD 2534"
    )
    assert normalized == "KING SOOPERS CASTLE ROCK CO"


@pytest.mark.parametrize(
    ("csv_bytes", "message"),
    [
        (b"Date,Amount,Description\n2026-04-01,abc,Music Subscription\n", "invalid amount"),
        (b"Date,Amount,Description\n2026-99-01,-10.00,Music Subscription\n", "invalid date"),
        (b"only,two\ncolumns,here\n", "logical Date, Amount, and Description"),
    ],
)
def test_invalid_csv_raises_clear_errors(csv_bytes: bytes, message: str) -> None:
    with pytest.raises(IngestionError, match=message):
        load_transactions(csv_bytes)
