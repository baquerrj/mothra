from __future__ import annotations

from datetime import date, timedelta

import pytest

from spending_visualizer.domain.models import AccountType, Transaction
from tests.support import build_account_descriptor, build_transaction


@pytest.fixture
def sample_csv_bytes() -> bytes:
    return (
        b"Date,Amount,Description\n"
        b"2026-01-03,1500.00,Payroll Employer Inc\n"
        b"2026-01-05,-100.00,Rent Payment\n"
        b"2026-01-15,-50.00,Streaming Service\n"
        b"2026-01-03,-120.00,CITI CARD ONLINE PAYMENT\n"
        b"2026-02-03,1500.00,Payroll Employer Inc\n"
        b"2026-02-05,-100.00,Rent Payment\n"
        b"2026-02-15,-55.00,Streaming Service\n"
        b"2026-02-04,-150.00,CITI CARD ONLINE PAYMENT\n"
        b"2026-03-03,1500.00,Payroll Employer Inc\n"
        b"2026-03-05,-100.00,Rent Payment\n"
        b"2026-03-15,-60.00,Streaming Service\n"
        b"2026-03-05,-180.00,CITI CARD ONLINE PAYMENT\n"
    )


@pytest.fixture
def sample_credit_card_csv_bytes() -> bytes:
    return (
        b"DATE,DESCRIPTION,AMOUNT,CHECK #,STATUS\n"
        b"01/04/2026,ONLINE PAYMENT THANK YOU,120.00,,Posted\n"
        b"01/10/2026,INTEREST CHARGE ON PURCHASES,-10.00,,Posted\n"
        b"01/15/2026,NETFLIX,-15.99,,Posted\n"
        b"02/05/2026,ONLINE PAYMENT THANK YOU,150.00,,Posted\n"
        b"02/10/2026,INTEREST CHARGE ON PURCHASES,-9.50,,Posted\n"
        b"02/15/2026,NETFLIX,-16.99,,Posted\n"
        b"03/06/2026,ONLINE PAYMENT THANK YOU,180.00,,Posted\n"
        b"03/10/2026,INTEREST CHARGE ON PURCHASES,-9.75,,Posted\n"
        b"03/15/2026,NETFLIX,-17.99,,Posted\n"
        b"03/20/2026,LATE FEE,-35.00,,Posted\n"
    )


@pytest.fixture
def sample_checking_filename() -> str:
    return "wellsfargo__checking__1234.csv"


@pytest.fixture
def sample_credit_card_filename() -> str:
    return "wellsfargo__creditcard__9876.csv"


@pytest.fixture
def recurring_transactions() -> tuple[Transaction, ...]:
    base = date(2026, 1, 5)
    checking_account = build_account_descriptor()
    payroll_account = build_account_descriptor(
        account_type=AccountType.CHECKING,
        account_number="1111",
        fingerprint="payroll-fixture",
    )
    items = [
        build_transaction(
            when=base + timedelta(days=30 * idx),
            amount="-20.00",
            description_raw=(
                f"RECURRING PAYMENT AUTHORIZED ON 01/0{idx + 1} "
                "STREAMING SERVICE CARD 1234"
            ),
            description_normalized="STREAMING SERVICE",
            source_row=idx + 1,
            account=checking_account,
        )
        for idx in range(4)
    ]
    payroll = [
        build_transaction(
            when=date(2026, 1, 3) + timedelta(days=14 * idx),
            amount="1500.00",
            description_raw="PAYROLL EMPLOYER INC",
            description_normalized="PAYROLL EMPLOYER INC",
            source_row=20 + idx,
            account=payroll_account,
        )
        for idx in range(4)
    ]
    return tuple(items + payroll)
