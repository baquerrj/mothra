from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from spending_visualizer.analysis.credit_card import (
    estimate_interest_rate,
    identify_credit_card_payments,
    identify_interest_transactions,
    identify_late_fee_transactions,
)
from spending_visualizer.analysis.insights import build_insights
from spending_visualizer.analysis.monthly import summarize_monthly
from spending_visualizer.analysis.payment_matching import match_credit_card_payments
from spending_visualizer.analysis.recurring import detect_recurring_candidates
from spending_visualizer.config import AnalysisConfig
from spending_visualizer.domain.models import (
    AccountAnalysisReport,
    AccountType,
    CrossAccountReport,
    DashboardReport,
    Direction,
    OverrideDecision,
    RecurringCandidate,
    RecurringExpenseBreakdownRow,
    RecurringType,
    Transaction,
)
from spending_visualizer.ingest.csv_loader import ParsedTransactions, load_transactions
from spending_visualizer.persistence.overrides import OverrideStore


@dataclass(frozen=True)
class AccountReportBundle:
    report: AccountAnalysisReport
    recurring_expense_total: Decimal
    fixed_recurring_expense_total: Decimal
    variable_recurring_expense_total: Decimal
    recurring_credit_total: Decimal


@dataclass(frozen=True)
class DashboardBundle:
    report: DashboardReport
    checking_bundle: AccountReportBundle | None
    credit_card_bundle: AccountReportBundle | None


def build_report(
    file_bytes: bytes,
    filename: str,
    override_store: OverrideStore,
    config: AnalysisConfig | None = None,
) -> AccountReportBundle:
    analysis_config = config or AnalysisConfig()
    parsed = load_transactions(file_bytes, filename)
    decisions = override_store.get_decisions(parsed.account.storage_key)
    return build_report_from_parsed(parsed, decisions, analysis_config)


def build_dashboard_bundle(
    checking_parsed: ParsedTransactions | None,
    credit_card_parsed: ParsedTransactions | None,
    override_store: OverrideStore,
    config: AnalysisConfig | None = None,
) -> DashboardBundle:
    analysis_config = config or AnalysisConfig()
    recurring_decisions: dict[str, dict[str, OverrideDecision]] = {}
    if checking_parsed is not None:
        recurring_decisions[checking_parsed.account.storage_key] = override_store.get_decisions(
            checking_parsed.account.storage_key
        )
    if credit_card_parsed is not None:
        recurring_decisions[credit_card_parsed.account.storage_key] = override_store.get_decisions(
            credit_card_parsed.account.storage_key
        )
    payment_match_decisions: dict[str, OverrideDecision] = {}
    if checking_parsed is not None and credit_card_parsed is not None:
        payment_scope_key = build_payment_match_scope_key(
            checking_parsed.account.storage_key,
            credit_card_parsed.account.storage_key,
        )
        payment_match_decisions = override_store.get_payment_match_decisions(payment_scope_key)
    return build_dashboard_bundle_from_parsed(
        checking_parsed=checking_parsed,
        credit_card_parsed=credit_card_parsed,
        recurring_decisions=recurring_decisions,
        payment_match_decisions=payment_match_decisions,
        config=analysis_config,
    )


def build_dashboard_bundle_from_parsed(
    checking_parsed: ParsedTransactions | None,
    credit_card_parsed: ParsedTransactions | None,
    recurring_decisions: dict[str, dict[str, OverrideDecision]],
    payment_match_decisions: dict[str, OverrideDecision],
    config: AnalysisConfig | None = None,
) -> DashboardBundle:
    analysis_config = config or AnalysisConfig()
    checking_bundle = (
        build_report_from_parsed(
            checking_parsed,
            recurring_decisions.get(checking_parsed.account.storage_key, {}),
            analysis_config,
        )
        if checking_parsed is not None
        else None
    )
    credit_card_bundle = (
        build_report_from_parsed(
            credit_card_parsed,
            recurring_decisions.get(credit_card_parsed.account.storage_key, {}),
            analysis_config,
        )
        if credit_card_parsed is not None
        else None
    )

    cross_account_report = None
    if checking_bundle is not None and credit_card_bundle is not None:
        matches = match_credit_card_payments(
            checking_transactions=checking_bundle.report.transactions,
            credit_card_payments=credit_card_bundle.report.payment_credits,
            decisions=payment_match_decisions,
            config=analysis_config,
        )
        cross_account_report = CrossAccountReport(
            checking_account=checking_bundle.report.account,
            credit_card_account=credit_card_bundle.report.account,
            payment_matches=matches,
            matched_payment_total=sum(
                (match.credit_card_transaction.amount for match in matches),
                Decimal("0.00"),
            ).quantize(Decimal("0.01")),
        )

    return DashboardBundle(
        report=DashboardReport(
            checking_report=checking_bundle.report if checking_bundle is not None else None,
            credit_card_report=(
                credit_card_bundle.report if credit_card_bundle is not None else None
            ),
            cross_account_report=cross_account_report,
        ),
        checking_bundle=checking_bundle,
        credit_card_bundle=credit_card_bundle,
    )


def build_report_from_parsed(
    parsed: ParsedTransactions,
    decisions: dict[str, OverrideDecision],
    config: AnalysisConfig | None = None,
) -> AccountReportBundle:
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
    variable_recurring_debits = tuple(
        candidate
        for candidate in recurring_debits
        if candidate.recurring_type == RecurringType.VARIABLE
    )
    recurring_expense_breakdown = build_recurring_expense_breakdown(recurring_debits)
    interest_transactions: tuple[Transaction, ...] = ()
    late_fee_transactions: tuple[Transaction, ...] = ()
    payment_credits: tuple[Transaction, ...] = ()
    interest_estimate = None
    if parsed.account.account_type == AccountType.CREDITCARD:
        interest_transactions = identify_interest_transactions(parsed.transactions)
        late_fee_transactions = identify_late_fee_transactions(parsed.transactions)
        payment_credits = identify_credit_card_payments(parsed.transactions)
        interest_estimate = estimate_interest_rate(parsed.transactions, analysis_config)
    insights = build_insights(parsed.transactions, monthly_summaries)
    report = AccountAnalysisReport(
        account=parsed.account,
        transactions=parsed.transactions,
        monthly_summaries=monthly_summaries,
        recurring_debits=recurring_debits,
        variable_recurring_debits=variable_recurring_debits,
        recurring_credits=recurring_credits,
        recurring_expense_breakdown=recurring_expense_breakdown,
        insights=insights,
        payment_credits=payment_credits,
        interest_transactions=interest_transactions,
        late_fee_transactions=late_fee_transactions,
        interest_estimate=interest_estimate,
    )
    recurring_expense_total = sum(
        (candidate.estimated_monthly_amount for candidate in recurring_debits),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))
    fixed_recurring_expense_total = sum(
        (
            candidate.estimated_monthly_amount
            for candidate in recurring_debits
            if candidate.recurring_type == RecurringType.FIXED
        ),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))
    variable_recurring_expense_total = sum(
        (
            candidate.estimated_monthly_amount
            for candidate in recurring_debits
            if candidate.recurring_type == RecurringType.VARIABLE
        ),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))
    recurring_credit_total = sum(
        (candidate.estimated_monthly_amount for candidate in recurring_credits),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))
    return AccountReportBundle(
        report=report,
        recurring_expense_total=recurring_expense_total,
        fixed_recurring_expense_total=fixed_recurring_expense_total,
        variable_recurring_expense_total=variable_recurring_expense_total,
        recurring_credit_total=recurring_credit_total,
    )


def build_recurring_expense_breakdown(
    candidates: tuple[RecurringCandidate, ...],
) -> tuple[RecurringExpenseBreakdownRow, ...]:
    rows = [
        RecurringExpenseBreakdownRow(
            merchant_label=candidate.merchant_label,
            cadence=candidate.cadence,
            recurring_type=candidate.recurring_type,
            estimated_monthly_amount=candidate.estimated_monthly_amount,
            amount_average=candidate.amount_average,
            amount_min=candidate.amount_min,
            amount_max=candidate.amount_max,
            occurrences=candidate.occurrences,
            confidence=candidate.confidence,
        )
        for candidate in candidates
    ]
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.estimated_monthly_amount,
                row.recurring_type.value,
                row.merchant_label,
            ),
        )
    )


def apply_overrides(
    candidates: tuple[RecurringCandidate, ...],
    decisions: dict[str, OverrideDecision],
) -> tuple[RecurringCandidate, ...]:
    included: list[RecurringCandidate] = []
    for candidate in candidates:
        if (
            decisions.get(candidate.candidate_id, OverrideDecision.AUTO)
            == OverrideDecision.REJECTED
        ):
            continue
        included.append(candidate)
    return tuple(included)


def build_payment_match_scope_key(checking_scope: str, credit_card_scope: str) -> str:
    return f"{checking_scope}__{credit_card_scope}"
