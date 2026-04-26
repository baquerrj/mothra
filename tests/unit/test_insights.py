from __future__ import annotations

from datetime import date

from spending_visualizer.analysis.insights import build_insights
from spending_visualizer.analysis.monthly import summarize_monthly
from tests.support import build_transaction


def test_build_insights_emits_budgeting_signals() -> None:
    transactions = (
        build_transaction(when=date(2026, 1, 2), amount="3000.00", description_raw="Payroll"),
        build_transaction(when=date(2026, 1, 5), amount="-1000.00", description_raw="Rent"),
        build_transaction(when=date(2026, 2, 5), amount="-2000.00", description_raw="Travel"),
        build_transaction(when=date(2026, 2, 6), amount="1000.00", description_raw="Side Gig"),
    )
    summaries = summarize_monthly(transactions)
    insights = build_insights(transactions, summaries)
    types = {insight.insight_type for insight in insights}
    assert "cash_flow_high" in types
    assert "cash_flow_low" in types
    assert "spend_concentration" in types
    assert "income_variability" in types
