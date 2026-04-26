from __future__ import annotations

from datetime import date
from decimal import Decimal

from spending_visualizer.domain.models import Direction, Transaction


def build_transaction(
    *,
    when: date,
    amount: str,
    description_raw: str,
    description_normalized: str | None = None,
    source_row: int = 1,
) -> Transaction:
    decimal_amount = Decimal(amount)
    return Transaction(
        date=when,
        amount=decimal_amount,
        description_raw=description_raw,
        description_normalized=description_normalized or description_raw.upper(),
        direction=Direction.CREDIT if decimal_amount >= Decimal("0.00") else Direction.DEBIT,
        source_row=source_row,
    )
