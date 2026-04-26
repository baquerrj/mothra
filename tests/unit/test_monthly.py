from __future__ import annotations

from datetime import date
from decimal import Decimal

from spending_visualizer.analysis.monthly import summarize_monthly
from tests.support import build_transaction


def test_summarize_monthly_totals() -> None:
    transactions = (
        build_transaction(when=date(2026, 1, 2), amount="2000.00", description_raw="Payroll"),
        build_transaction(when=date(2026, 1, 5), amount="-500.00", description_raw="Rent"),
        build_transaction(when=date(2026, 2, 5), amount="-250.00", description_raw="Utilities"),
    )
    summaries = summarize_monthly(transactions)
    assert summaries[0].month == "2026-01"
    assert summaries[0].total_in == Decimal("2000.00")
    assert summaries[0].total_out == Decimal("500.00")
    assert summaries[0].net == Decimal("1500.00")
    assert summaries[1].net == Decimal("-250.00")
