from __future__ import annotations

from decimal import Decimal

from spending_visualizer.config import AnalysisConfig
from spending_visualizer.domain.models import OverrideDecision, PaymentMatchCandidate, Transaction


def match_credit_card_payments(
    checking_transactions: tuple[Transaction, ...],
    credit_card_payments: tuple[Transaction, ...],
    decisions: dict[str, OverrideDecision],
    config: AnalysisConfig,
) -> tuple[PaymentMatchCandidate, ...]:
    matches: list[PaymentMatchCandidate] = []
    used_checking_rows: set[int] = set()
    used_card_rows: set[int] = set()
    candidates: list[tuple[float, Transaction, Transaction, str]] = []

    for checking_tx in checking_transactions:
        if checking_tx.amount >= 0:
            continue
        for card_tx in credit_card_payments:
            confidence = score_payment_match(checking_tx, card_tx, config)
            if confidence < config.payment_match_min_confidence:
                continue
            evidence = build_match_evidence(checking_tx, card_tx)
            candidates.append((confidence, checking_tx, card_tx, evidence))

    for confidence, checking_tx, card_tx, evidence in sorted(
        candidates,
        key=lambda item: (-item[0], abs((item[2].date - item[1].date).days), item[1].source_row),
    ):
        match_id = build_match_id(checking_tx, card_tx)
        status = decisions.get(match_id, OverrideDecision.AUTO)
        if status == OverrideDecision.REJECTED:
            continue
        if checking_tx.source_row in used_checking_rows:
            continue
        if card_tx.source_row in used_card_rows:
            continue
        used_checking_rows.add(checking_tx.source_row)
        used_card_rows.add(card_tx.source_row)
        adjusted_confidence = (
            min(confidence + 0.15, 0.99)
            if status == OverrideDecision.CONFIRMED
            else confidence
        )
        matches.append(
            PaymentMatchCandidate(
                match_id=match_id,
                checking_transaction=checking_tx,
                credit_card_transaction=card_tx,
                confidence=round(adjusted_confidence, 2),
                evidence=evidence,
                status=status,
            )
        )

    return tuple(matches)


def score_payment_match(
    checking_tx: Transaction,
    card_tx: Transaction,
    config: AnalysisConfig,
) -> float:
    amount_delta = abs(abs(checking_tx.amount) - card_tx.amount)
    if amount_delta > Decimal("1.00"):
        return 0.0
    day_gap = abs((card_tx.date - checking_tx.date).days)
    if day_gap > config.payment_match_window_days:
        return 0.0
    confidence = 0.55
    if amount_delta == Decimal("0.00"):
        confidence += 0.25
    elif amount_delta <= Decimal("0.25"):
        confidence += 0.15
    confidence += max(0.0, (config.payment_match_window_days - day_gap) * 0.03)
    if (
        "PAYMENT" in checking_tx.description_normalized
        or "EPAY" in checking_tx.description_normalized
    ):
        confidence += 0.10
    return min(confidence, 0.99)


def build_match_evidence(checking_tx: Transaction, card_tx: Transaction) -> str:
    amount_delta = abs(abs(checking_tx.amount) - card_tx.amount).quantize(Decimal("0.01"))
    day_gap = abs((card_tx.date - checking_tx.date).days)
    return (
        f"Amount delta ${amount_delta}, posting gap {day_gap} days, "
        f"checking descriptor {checking_tx.description_normalized!r}."
    )


def build_match_id(checking_tx: Transaction, card_tx: Transaction) -> str:
    return (
        f"{checking_tx.account.storage_key}:{checking_tx.source_row}:"
        f"{card_tx.account.storage_key}:{card_tx.source_row}"
    )
