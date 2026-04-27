from __future__ import annotations

from datetime import date
from decimal import Decimal

from spending_visualizer.domain.models import AccountDescriptor, AccountType, Direction, Transaction


def build_account_descriptor(
    *,
    bank_name: str = "wellsfargo",
    account_type: AccountType = AccountType.CHECKING,
    account_number: str = "0000",
    fingerprint: str = "fixture-fingerprint",
    source_filename: str | None = None,
) -> AccountDescriptor:
    filename = source_filename or f"{bank_name}__{account_type.value}__{account_number}.csv"
    return AccountDescriptor(
        source_filename=filename,
        bank_name=bank_name,
        account_type=account_type,
        account_number=account_number,
        fingerprint=fingerprint,
    )


def build_transaction(
    *,
    when: date,
    amount: str,
    description_raw: str,
    description_normalized: str | None = None,
    source_row: int = 1,
    account: AccountDescriptor | None = None,
) -> Transaction:
    decimal_amount = Decimal(amount)
    return Transaction(
        account=account or build_account_descriptor(),
        date=when,
        amount=decimal_amount,
        description_raw=description_raw,
        description_normalized=description_normalized or description_raw.upper(),
        direction=Direction.CREDIT if decimal_amount >= Decimal("0.00") else Direction.DEBIT,
        source_row=source_row,
    )
