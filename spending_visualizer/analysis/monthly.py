from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from spending_visualizer.domain.models import MonthlySummary, Transaction


def summarize_monthly(transactions: tuple[Transaction, ...]) -> tuple[MonthlySummary, ...]:
    buckets: dict[str, list[Decimal]] = defaultdict(list)
    for transaction in transactions:
        month = transaction.date.strftime("%Y-%m")
        buckets[month].append(transaction.amount)

    summaries = []
    for month in sorted(buckets):
        total_in = sum((amount for amount in buckets[month] if amount > 0), Decimal("0.00"))
        total_out = sum((-amount for amount in buckets[month] if amount < 0), Decimal("0.00"))
        summaries.append(
            MonthlySummary(
                month=month,
                total_in=total_in.quantize(Decimal("0.01")),
                total_out=total_out.quantize(Decimal("0.01")),
                net=(total_in - total_out).quantize(Decimal("0.01")),
            )
        )
    return tuple(summaries)
