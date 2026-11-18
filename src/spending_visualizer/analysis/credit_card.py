from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from spending_visualizer.config import AnalysisConfig
from spending_visualizer.domain.models import InterestEstimate, Transaction

INTEREST_DESCRIPTION = "INTEREST CHARGE ON PURCHASES"
LATE_FEE_DESCRIPTION = "LATE FEE"
PAYMENT_DESCRIPTION = "ONLINE PAYMENT THANK YOU"


def identify_interest_transactions(
    transactions: tuple[Transaction, ...],
) -> tuple[Transaction, ...]:
    return tuple(
        transaction
        for transaction in transactions
        if transaction.description_normalized == INTEREST_DESCRIPTION
    )


def identify_late_fee_transactions(
    transactions: tuple[Transaction, ...],
) -> tuple[Transaction, ...]:
    return tuple(
        transaction
        for transaction in transactions
        if transaction.description_normalized == LATE_FEE_DESCRIPTION
    )


def identify_credit_card_payments(transactions: tuple[Transaction, ...]) -> tuple[Transaction, ...]:
    return tuple(
        transaction
        for transaction in transactions
        if transaction.amount > 0 and PAYMENT_DESCRIPTION in transaction.description_normalized
    )


def estimate_interest_rate(
    transactions: tuple[Transaction, ...],
    config: AnalysisConfig,
) -> InterestEstimate | None:
    monthly_interest: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    monthly_end_balances: dict[str, Decimal] = {}
    running_balance = Decimal("0.00")
    ordered = sorted(transactions, key=lambda item: (item.date, item.source_row))

    for transaction in ordered:
        month = transaction.date.strftime("%Y-%m")
        amount = abs(transaction.amount) if transaction.amount < 0 else -transaction.amount
        running_balance += amount
        if transaction.description_normalized == INTEREST_DESCRIPTION:
            monthly_interest[month] += abs(transaction.amount)
        monthly_end_balances[month] = running_balance

    months = sorted(monthly_end_balances)
    if not months:
        return None

    monthly_rates: list[Decimal] = []
    previous_balance = Decimal("0.00")
    for month in months:
        interest = monthly_interest.get(month, Decimal("0.00"))
        if interest > 0 and previous_balance > 0:
            monthly_rates.append(
                ((interest / previous_balance) * Decimal("1200")).quantize(
                    Decimal("0.01")
                )
            )
        previous_balance = max(monthly_end_balances[month], Decimal("0.00"))

    recent_interest_months = [
        monthly_interest[month]
        for month in months
        if monthly_interest[month] > 0
    ]
    if not recent_interest_months:
        return None

    current_apr = monthly_rates[-1] if monthly_rates else None
    recent_rates = monthly_rates[-config.recent_interest_months :] if monthly_rates else []
    recent_average_apr = (
        (sum(recent_rates, Decimal("0.00")) / Decimal(len(recent_rates))).quantize(Decimal("0.01"))
        if recent_rates
        else None
    )
    recent_interest_average = (
        sum(recent_interest_months[-config.recent_interest_months :], Decimal("0.00"))
        / Decimal(min(len(recent_interest_months), config.recent_interest_months))
    ).quantize(Decimal("0.01"))
    confidence_label = "medium" if len(monthly_rates) >= 3 else "low"
    trend_summary = build_interest_trend_summary(recent_rates)
    caveat = (
        "Approximate APR derived from interest charges and an inferred carried balance proxy; "
        "statement balances are not available in the CSV."
    )
    return InterestEstimate(
        current_apr=current_apr,
        recent_average_apr=recent_average_apr,
        recent_interest_average=recent_interest_average,
        confidence_label=confidence_label,
        trend_summary=trend_summary,
        caveat=caveat,
    )


def build_interest_trend_summary(recent_rates: list[Decimal]) -> str:
    if len(recent_rates) < 2:
        return "Not enough interest-charge history to infer an APR trend."
    if recent_rates[-1] > recent_rates[0]:
        return "Estimated APR trend is increasing over recent months."
    if recent_rates[-1] < recent_rates[0]:
        return "Estimated APR trend is decreasing over recent months."
    return "Estimated APR trend is broadly flat over recent months."
