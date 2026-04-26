from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from statistics import median

from spending_visualizer.config import AnalysisConfig, CadenceRule
from spending_visualizer.domain.models import Direction, RecurringCandidate, Transaction


def detect_recurring_candidates(
    transactions: tuple[Transaction, ...],
    direction: Direction,
    config: AnalysisConfig,
) -> tuple[RecurringCandidate, ...]:
    filtered = tuple(
        transaction for transaction in transactions if transaction.direction == direction
    )
    grouped: dict[str, list[Transaction]] = defaultdict(list)
    for transaction in filtered:
        grouped[transaction.description_normalized].append(transaction)

    candidates: list[RecurringCandidate] = []
    for fingerprint, group in grouped.items():
        ordered = tuple(sorted(group, key=lambda item: (item.date, item.amount, item.source_row)))
        if len(ordered) < config.minimum_occurrences:
            continue
        cadence = infer_cadence(ordered, config)
        if cadence is None:
            continue
        candidate = build_candidate(ordered, fingerprint, direction, cadence, config)
        if candidate.confidence >= config.minimum_confidence:
            candidates.append(candidate)

    return tuple(sorted(candidates, key=lambda item: (-item.confidence, item.merchant_label)))


def infer_cadence(
    transactions: tuple[Transaction, ...],
    config: AnalysisConfig,
) -> CadenceRule | None:
    intervals = [
        (later.date - earlier.date).days
        for earlier, later in zip(transactions, transactions[1:], strict=False)
    ]
    if not intervals:
        return None
    best_rule: CadenceRule | None = None
    best_score = -1.0
    for rule in config.cadence_rules:
        matches = sum(
            1
            for interval in intervals
            if abs(interval - rule.interval_days) <= rule.tolerance_days
        )
        score = matches / len(intervals)
        if score > best_score:
            best_score = score
            best_rule = rule
    if best_rule is None or best_score < 0.6:
        return None
    return best_rule


def build_candidate(
    transactions: tuple[Transaction, ...],
    fingerprint: str,
    direction: Direction,
    cadence: CadenceRule,
    config: AnalysisConfig,
) -> RecurringCandidate:
    amounts = [abs(transaction.amount) for transaction in transactions]
    typical_amount = median(amounts)
    tolerance = max(
        Decimal(str(config.amount_variance_floor)),
        typical_amount * Decimal(str(config.amount_variance_ratio)),
    ).quantize(Decimal("0.01"))
    stable_matches = sum(1 for amount in amounts if abs(amount - typical_amount) <= tolerance)
    amount_score = stable_matches / len(amounts)
    intervals = [
        (later.date - earlier.date).days
        for earlier, later in zip(transactions, transactions[1:], strict=False)
    ]
    cadence_score = (
        sum(
            1
            for interval in intervals
            if abs(interval - cadence.interval_days) <= cadence.tolerance_days
        )
        / len(intervals)
    )
    occurrence_score = min(len(transactions) / 6, 1.0)
    confidence = round(
        (amount_score * 0.35) + (cadence_score * 0.45) + (occurrence_score * 0.20),
        2,
    )
    expected_window = build_expected_window(transactions, cadence)
    candidate_id = f"{direction.value}:{fingerprint}:{cadence.name}"
    annual_multiplier = Decimal(cadence.annual_occurrences) / Decimal("12")
    estimated_monthly_amount = (typical_amount * annual_multiplier).quantize(Decimal("0.01"))
    return RecurringCandidate(
        candidate_id=candidate_id,
        kind=direction,
        fingerprint=fingerprint,
        merchant_label=fingerprint.title(),
        cadence=cadence.name,
        expected_day_window=expected_window,
        typical_amount=typical_amount.quantize(Decimal("0.01")),
        amount_tolerance=tolerance,
        occurrences=len(transactions),
        confidence=confidence,
        estimated_monthly_amount=estimated_monthly_amount,
        transactions=transactions,
    )


def build_expected_window(transactions: tuple[Transaction, ...], cadence: CadenceRule) -> str:
    days = sorted(transaction.date.day for transaction in transactions)
    if cadence.name == "monthly":
        start = max(min(days) - cadence.tolerance_days, 1)
        end = min(max(days) + cadence.tolerance_days, 31)
        return f"days {start}-{end}"
    if cadence.name == "biweekly":
        return "every 11-17 days"
    return "every 5-9 days"
