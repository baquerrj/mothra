from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from statistics import mean, median

from spending_visualizer.config import AnalysisConfig, CadenceRule
from spending_visualizer.domain.models import (
    Direction,
    RecurringCandidate,
    RecurringType,
    Transaction,
)


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
        candidate = build_candidate(
            ordered,
            fingerprint,
            direction,
            cadence,
            classify_amount_pattern(ordered, config),
            config,
        )
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


def classify_amount_pattern(
    transactions: tuple[Transaction, ...],
    config: AnalysisConfig,
) -> RecurringType:
    amounts = [abs(transaction.amount) for transaction in transactions]
    typical_amount = median(amounts)
    tolerance = max(
        Decimal(str(config.amount_variance_floor)),
        typical_amount * Decimal(str(config.amount_variance_ratio)),
    ).quantize(Decimal("0.01"))
    stable_matches = sum(1 for amount in amounts if abs(amount - typical_amount) <= tolerance)
    amount_match_ratio = stable_matches / len(amounts)
    amount_span = max(amounts) - min(amounts)
    span_ratio = (
        amount_span / typical_amount if typical_amount != Decimal("0.00") else Decimal("0.00")
    )
    unique_amounts = len(set(amounts))
    if (
        amount_match_ratio >= config.fixed_amount_match_ratio
        and span_ratio < Decimal(str(config.variable_amount_ratio_floor))
    ):
        return RecurringType.FIXED
    if unique_amounts >= config.variable_min_unique_amounts:
        return RecurringType.VARIABLE
    return RecurringType.FIXED


def build_candidate(
    transactions: tuple[Transaction, ...],
    fingerprint: str,
    direction: Direction,
    cadence: CadenceRule,
    recurring_type: RecurringType,
    config: AnalysisConfig,
) -> RecurringCandidate:
    amounts = [abs(transaction.amount) for transaction in transactions]
    typical_amount = median(amounts)
    average_amount = Decimal(str(mean(amounts))).quantize(Decimal("0.01"))
    amount_min = min(amounts).quantize(Decimal("0.01"))
    amount_max = max(amounts).quantize(Decimal("0.01"))
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
    baseline_amount = average_amount if recurring_type == RecurringType.VARIABLE else typical_amount
    estimated_monthly_amount = (baseline_amount * annual_multiplier).quantize(Decimal("0.01"))
    return RecurringCandidate(
        candidate_id=candidate_id,
        kind=direction,
        fingerprint=fingerprint,
        merchant_label=fingerprint.title(),
        recurring_type=recurring_type,
        cadence=cadence.name,
        expected_day_window=expected_window,
        typical_amount=typical_amount.quantize(Decimal("0.01")),
        amount_average=average_amount,
        amount_min=amount_min,
        amount_max=amount_max,
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
