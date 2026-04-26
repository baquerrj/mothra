from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal

from spending_visualizer.domain.models import (
    Direction,
    Insight,
    InsightSeverity,
    MonthlySummary,
    Transaction,
)


def build_insights(
    transactions: tuple[Transaction, ...],
    monthly_summaries: tuple[MonthlySummary, ...],
) -> tuple[Insight, ...]:
    insights: list[Insight] = []
    insights.extend(cash_flow_insights(monthly_summaries))
    insights.extend(concentration_insights(transactions))
    insights.extend(spend_spike_insights(monthly_summaries))
    insights.extend(income_variability_insights(monthly_summaries))
    return tuple(insights)


def cash_flow_insights(monthly_summaries: tuple[MonthlySummary, ...]) -> list[Insight]:
    if not monthly_summaries:
        return []
    best = max(monthly_summaries, key=lambda item: item.net)
    worst = min(monthly_summaries, key=lambda item: item.net)
    return [
        Insight(
            insight_type="cash_flow_high",
            severity=InsightSeverity.POSITIVE,
            message=f"Best net cash-flow month: {best.month}",
            evidence=f"Net cash flow was ${best.net:.2f}.",
        ),
        Insight(
            insight_type="cash_flow_low",
            severity=InsightSeverity.WARNING,
            message=f"Weakest net cash-flow month: {worst.month}",
            evidence=f"Net cash flow was ${worst.net:.2f}.",
        ),
    ]


def concentration_insights(transactions: tuple[Transaction, ...]) -> list[Insight]:
    spend_by_merchant: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    total_spend = Decimal("0.00")
    for transaction in transactions:
        if transaction.direction != Direction.DEBIT:
            continue
        spend = abs(transaction.amount)
        spend_by_merchant[transaction.description_normalized] += spend
        total_spend += spend
    if total_spend == Decimal("0.00") or not spend_by_merchant:
        return []
    top_merchant, top_amount = max(spend_by_merchant.items(), key=lambda item: item[1])
    share = (top_amount / total_spend) * Decimal("100")
    severity = InsightSeverity.WARNING if share >= Decimal("15") else InsightSeverity.INFO
    return [
        Insight(
            insight_type="spend_concentration",
            severity=severity,
            message=f"Top merchant by spend: {top_merchant.title()}",
            evidence=f"It represents {share.quantize(Decimal('0.01'))}% of total outflows.",
        )
    ]


def spend_spike_insights(monthly_summaries: tuple[MonthlySummary, ...]) -> list[Insight]:
    if len(monthly_summaries) < 2:
        return []
    prior_months = monthly_summaries[:-1]
    average_out = sum((item.total_out for item in prior_months), Decimal("0.00")) / Decimal(
        len(prior_months)
    )
    latest = monthly_summaries[-1]
    if average_out == Decimal("0.00"):
        return []
    ratio = latest.total_out / average_out
    if ratio < Decimal("1.20"):
        return []
    return [
        Insight(
            insight_type="spend_spike",
            severity=InsightSeverity.WARNING,
            message=f"Spending spiked in {latest.month}",
            evidence=(
                f"Monthly outflows were {ratio.quantize(Decimal('0.01'))}x "
                "the prior baseline."
            ),
        )
    ]


def income_variability_insights(monthly_summaries: tuple[MonthlySummary, ...]) -> list[Insight]:
    if len(monthly_summaries) < 2:
        return []
    incomes = [item.total_in for item in monthly_summaries if item.total_in > 0]
    if len(incomes) < 2:
        return []
    average_income = sum(incomes, Decimal("0.00")) / Decimal(len(incomes))
    if average_income == Decimal("0.00"):
        return []
    low_months = Counter(
        summary.month
        for summary in monthly_summaries
        if summary.total_in < average_income * Decimal("0.75")
    )
    if not low_months:
        return []
    month = next(iter(low_months))
    return [
        Insight(
            insight_type="income_variability",
            severity=InsightSeverity.INFO,
            message="Income is variable month to month",
            evidence=f"{month} fell more than 25% below average monthly inflows.",
        )
    ]
