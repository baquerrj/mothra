from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from spending_visualizer.domain.models import Transaction
from tests.support import build_transaction


@pytest.fixture
def sample_csv_bytes() -> bytes:
    return Path("Checking1.csv").read_bytes()


@pytest.fixture
def recurring_transactions() -> tuple[Transaction, ...]:
    base = date(2026, 1, 5)
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
        )
        for idx in range(4)
    ]
    return tuple(items + payroll)
