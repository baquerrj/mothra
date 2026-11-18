from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from spending_visualizer.domain.models import AccountType
from spending_visualizer.ingest.csv_loader import (
    IngestionError,
    build_filename_error_message,
    load_transactions,
    normalize_description,
    parse_account_descriptor,
    validate_account_filename,
)
from spending_visualizer.logging_utils import configure_logging


def test_load_transactions_supports_headered_csv(sample_checking_filename: str) -> None:
    csv_bytes = (
        b"Date,Amount,Description,Ignored\n"
        b"2026-04-01,-10.50,Music Subscription,foo\n"
        b"2026-04-02,1200.00,Payroll,bar\n"
    )
    parsed = load_transactions(csv_bytes, sample_checking_filename)
    assert parsed.account.account_type == AccountType.CHECKING
    assert len(parsed.transactions) == 2
    assert parsed.transactions[0].description_normalized == "MUSIC SUBSCRIPTION"


def test_load_transactions_supports_wells_fargo_style_csv(sample_checking_filename: str) -> None:
    csv_bytes = (
        b'"04/24/2026","-20.00","*","","RECURRING PAYMENT AUTHORIZED ON 04/21 '
        b'CLAUDE AI SUBSCRIPTION CARD 1234"\n'
    )
    parsed = load_transactions(csv_bytes, sample_checking_filename)
    assert parsed.transactions[0].description_normalized == "CLAUDE AI SUBSCRIPTION"


def test_load_transactions_supports_credit_card_csv(sample_credit_card_filename: str) -> None:
    csv_bytes = (
        b"DATE,DESCRIPTION,AMOUNT,CHECK #,STATUS\n"
        b"01/01/2026,ONLINE PAYMENT THANK YOU,250.00,,Posted\n"
        b"01/02/2026,INTEREST CHARGE ON PURCHASES,-18.50,,Posted\n"
    )
    parsed = load_transactions(csv_bytes, sample_credit_card_filename)
    assert parsed.account.account_type == AccountType.CREDITCARD
    assert parsed.transactions[0].posted_status == "Posted"
    assert parsed.transactions[0].amount == Decimal("250.00")
    assert parsed.transactions[1].description_normalized == "INTEREST CHARGE ON PURCHASES"


def test_transaction_normalization_uses_decimal_and_source_rows(
    sample_checking_filename: str,
) -> None:
    csv_bytes = b"Date,Amount,Description\n2026-04-01,-10.50,Music Subscription\n"
    parsed = load_transactions(csv_bytes, sample_checking_filename)
    transaction = parsed.transactions[0]
    assert transaction.amount == Decimal("-10.50")
    assert transaction.source_row == 2
    assert transaction.account.account_number == "1234"


def test_filename_parser_extracts_account_identity() -> None:
    descriptor = parse_account_descriptor(
        "wellsfargo__creditcard__9999.csv",
        "fixture-fingerprint",
    )
    assert descriptor.bank_name == "wellsfargo"
    assert descriptor.account_type == AccountType.CREDITCARD
    assert descriptor.account_number == "9999"


def test_normalize_description_removes_card_noise() -> None:
    normalized = normalize_description(
        "PURCHASE AUTHORIZED ON 04/22 KING SOOPERS #0132 CASTLE ROCK CO S356112860254084 CARD 2534"
    )
    assert normalized == "KING SOOPERS CASTLE ROCK CO"


@pytest.mark.parametrize(
    ("filename", "message"),
    [
        ("wf_checking_1888.csv", "single underscores"),
        ("wellsfargo__savings__1234.csv", "unsupported account_type"),
        ("wellsfargo__creditcard__.csv", "missing account_number"),
        ("wellsfargo__checking__1234.txt", "expected a .csv extension"),
    ],
)
def test_invalid_filename_raises_reason_specific_errors(
    filename: str,
    message: str,
) -> None:
    with pytest.raises(IngestionError, match=message):
        parse_account_descriptor(filename, "fixture")


def test_validate_account_filename_returns_structured_reason() -> None:
    validation = validate_account_filename("wf_checking_1888.csv")
    assert validation.is_valid is False
    assert validation.error_reason == "found single underscores instead of required '__' separators"
    assert "single underscores" in build_filename_error_message(validation)


def test_invalid_filename_emits_warning_log(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "ingest.log"
    monkeypatch.setenv("SPENDING_VISUALIZER_LOG_FILE", str(log_path))
    configure_logging()
    with pytest.raises(IngestionError):
        parse_account_descriptor("wf_checking_1888.csv", "fixture")
    contents = log_path.read_text(encoding="utf-8")
    assert "Filename validation failed" in contents
    assert "wf_checking_1888.csv" in contents
    assert "Music Subscription" not in contents


@pytest.mark.parametrize(
    ("csv_bytes", "message"),
    [
        (b"Date,Amount,Description\n2026-04-01,abc,Music Subscription\n", "invalid amount"),
        (b"Date,Amount,Description\n2026-99-01,-10.00,Music Subscription\n", "invalid date"),
        (b"only,two\ncolumns,here\n", "logical Date, Amount, and Description"),
    ],
)
def test_invalid_csv_raises_clear_errors(
    csv_bytes: bytes,
    message: str,
    sample_checking_filename: str,
) -> None:
    with pytest.raises(IngestionError, match=message):
        load_transactions(csv_bytes, sample_checking_filename)
