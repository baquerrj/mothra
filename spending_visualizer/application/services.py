from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from spending_visualizer.analysis.insights import build_insights
from spending_visualizer.analysis.monthly import summarize_monthly
from spending_visualizer.analysis.recurring import detect_recurring_candidates
from spending_visualizer.config import AnalysisConfig
from spending_visualizer.domain.models import (
    AnalysisReport,
    Direction,
    OverrideDecision,
    RecurringCandidate,
)
from spending_visualizer.ingest.csv_loader import ParsedTransactions, load_transactions
from spending_visualizer.persistence.overrides import OverrideStore


@dataclass(frozen=True)
class ReportBundle:
    report: AnalysisReport
    recurring_expense_total: Decimal
    recurring_credit_total: Decimal


def build_report(
    file_bytes: bytes,
    override_store: OverrideStore,
    config: AnalysisConfig | None = None,
) -> ReportBundle:
    analysis_config = config or AnalysisConfig()
    parsed = load_transactions(file_bytes)
    decisions = override_store.get_decisions(parsed.fingerprint)
    return build_report_from_parsed(parsed, decisions, analysis_config)


def build_report_from_parsed(
    parsed: ParsedTransactions,
    decisions: dict[str, OverrideDecision],
    config: AnalysisConfig | None = None,
) -> ReportBundle:
    analysis_config = config or AnalysisConfig()
    monthly_summaries = summarize_monthly(parsed.transactions)
    recurring_debits = apply_overrides(
        detect_recurring_candidates(parsed.transactions, Direction.DEBIT, analysis_config),
        decisions,
    )
    recurring_credits = apply_overrides(
        detect_recurring_candidates(parsed.transactions, Direction.CREDIT, analysis_config),
        decisions,
    )
    insights = build_insights(parsed.transactions, monthly_summaries)
    report = AnalysisReport(
        fingerprint=parsed.fingerprint,
        transactions=parsed.transactions,
        monthly_summaries=monthly_summaries,
        recurring_debits=recurring_debits,
        recurring_credits=recurring_credits,
        insights=insights,
    )
    recurring_expense_total = sum(
        (candidate.estimated_monthly_amount for candidate in recurring_debits),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))
    recurring_credit_total = sum(
        (candidate.estimated_monthly_amount for candidate in recurring_credits),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))
    return ReportBundle(
        report=report,
        recurring_expense_total=recurring_expense_total,
        recurring_credit_total=recurring_credit_total,
    )


def apply_overrides(
    candidates: tuple[RecurringCandidate, ...],
    decisions: dict[str, OverrideDecision],
) -> tuple[RecurringCandidate, ...]:
    included: list[RecurringCandidate] = []
    for candidate in candidates:
        decision = decisions.get(candidate.candidate_id, OverrideDecision.AUTO)
        if decision == OverrideDecision.REJECTED:
            continue
        included.append(candidate)
    return tuple(included)
