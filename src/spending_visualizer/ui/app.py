from __future__ import annotations

import io
import time
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

from spending_visualizer.application.services import (
    AccountReportBundle,
    DashboardBundle,
    build_dashboard_bundle_from_parsed,
    build_payment_match_scope_key,
)
from spending_visualizer.domain.models import (
    AccountAnalysisReport,
    AccountType,
    InsightSeverity,
    OverrideDecision,
    RecurringCandidate,
    RecurringExpenseBreakdownRow,
)
from spending_visualizer.ingest.csv_loader import (
    IngestionError,
    ParsedTransactions,
    load_transactions,
)
from spending_visualizer.persistence.overrides import (
    PAYMENT_MATCH_NAMESPACE,
    RECURRING_NAMESPACE,
    OverrideStore,
)

REFRESH_DEBOUNCE_SECONDS = 3.0
REFRESH_POLL_INTERVAL = "1s"
SAMPLE_CHECKING_FILENAME = "wellsfargo__checking__sample1234.csv"
SAMPLE_CREDIT_CARD_FILENAME = "wellsfargo__creditcard__sample5678.csv"


def main() -> None:
    st.set_page_config(page_title="Spending Visualizer", layout="wide")
    st.title("Spending Visualizer")
    st.caption(
        "Local-only account analysis with recurring payment detection, credit-card insights, "
        "and cross-account payment matching."
    )

    override_store = OverrideStore()
    checking_parsed, credit_card_parsed = load_selected_accounts()
    if checking_parsed is None and credit_card_parsed is None:
        st.info(
            "Upload a checking or credit-card CSV to begin. Filenames must match "
            "<bank>__<account_type>__<account_number>.csv. Data stays on this machine."
        )
        return

    pending_refreshes = collect_pending_refreshes(
        checking_parsed,
        credit_card_parsed,
        override_store,
    )
    bundle = build_dashboard_bundle_from_parsed(
        checking_parsed=checking_parsed,
        credit_card_parsed=credit_card_parsed,
        recurring_decisions=build_recurring_decision_map(
            checking_parsed,
            credit_card_parsed,
            override_store,
        ),
        payment_match_decisions=build_payment_match_decisions(
            checking_parsed,
            credit_card_parsed,
            override_store,
        ),
    )

    render_pending_refresh_notice(pending_refreshes)
    render_dashboard(bundle, override_store)


def load_selected_accounts() -> tuple[ParsedTransactions | None, ParsedTransactions | None]:
    upload_columns = st.columns(2)
    checking_upload = upload_columns[0].file_uploader(
        "Upload checking account CSV",
        type=["csv"],
        key="checking_upload",
    )
    credit_card_upload = upload_columns[1].file_uploader(
        "Upload credit card CSV",
        type=["csv"],
        key="credit_card_upload",
    )
    sample_columns = st.columns(2)
    load_checking_sample = sample_columns[0].button("Load bundled checking sample CSV")
    load_credit_sample = sample_columns[1].button("Load bundled credit-card sample CSV")

    checking_parsed = parse_selected_file(
        checking_upload.getvalue() if checking_upload is not None else None,
        checking_upload.name if checking_upload is not None else None,
        AccountType.CHECKING,
        fallback_path=Path("Checking1.csv") if load_checking_sample else None,
        fallback_filename=SAMPLE_CHECKING_FILENAME,
    )
    credit_card_parsed = parse_selected_file(
        credit_card_upload.getvalue() if credit_card_upload is not None else None,
        credit_card_upload.name if credit_card_upload is not None else None,
        AccountType.CREDITCARD,
        fallback_path=Path("CreditCard.csv") if load_credit_sample else None,
        fallback_filename=SAMPLE_CREDIT_CARD_FILENAME,
    )
    return checking_parsed, credit_card_parsed


def parse_selected_file(
    file_bytes: bytes | None,
    filename: str | None,
    expected_account_type: AccountType,
    *,
    fallback_path: Path | None,
    fallback_filename: str,
) -> ParsedTransactions | None:
    if file_bytes is None and fallback_path is None:
        return None
    if file_bytes is not None:
        raw_bytes = file_bytes
    else:
        assert fallback_path is not None
        raw_bytes = fallback_path.read_bytes()
    source_filename = filename if filename is not None else fallback_filename
    try:
        return load_transactions(
            raw_bytes,
            source_filename,
            expected_account_type=expected_account_type,
        )
    except IngestionError as exc:
        st.error(str(exc))
        return None


def render_dashboard(bundle: DashboardBundle, override_store: OverrideStore) -> None:
    tab_specs: list[tuple[str, Callable[[], None]]] = []
    if bundle.checking_bundle is not None:
        checking_bundle = bundle.checking_bundle

        def render_checking_tab() -> None:
            render_account_dashboard(checking_bundle, override_store)

        tab_specs.append(("Checking", render_checking_tab))
    if bundle.credit_card_bundle is not None:
        credit_card_bundle = bundle.credit_card_bundle

        def render_credit_card_tab() -> None:
            render_account_dashboard(credit_card_bundle, override_store)

        tab_specs.append(("Credit Card", render_credit_card_tab))
    if bundle.report.cross_account_report is not None:
        def render_cross_account_tab() -> None:
            render_cross_account_dashboard(bundle, override_store)

        tab_specs.append(("Cross-Account", render_cross_account_tab))

    if len(tab_specs) == 1:
        tab_specs[0][1]()
        return

    tabs = st.tabs([label for label, _ in tab_specs])
    for tab, (_, renderer) in zip(tabs, tab_specs, strict=False):
        with tab:
            renderer()


def render_account_dashboard(
    bundle: AccountReportBundle,
    override_store: OverrideStore,
) -> None:
    report = bundle.report
    st.subheader(account_heading(report))
    st.caption(
        f"Source file: {report.account.source_filename} | "
        f"Account #{report.account.account_number}"
    )

    monthly_df = monthly_dataframe(report)
    total_in = sum((summary.total_in for summary in report.monthly_summaries), Decimal("0.00"))
    total_out = sum((summary.total_out for summary in report.monthly_summaries), Decimal("0.00"))

    metric_columns = st.columns(5)
    metric_columns[0].metric("Months", len(report.monthly_summaries))
    metric_columns[1].metric("Total In", format_currency(total_in))
    metric_columns[2].metric("Total Out", format_currency(total_out))
    metric_columns[3].metric(
        "Recurring Monthly Expenses",
        format_currency(bundle.recurring_expense_total),
    )
    metric_columns[4].metric(
        "Variable Recurring Expenses",
        format_currency(bundle.variable_recurring_expense_total),
    )

    st.line_chart(
        monthly_df.set_index("month")[["total_in", "total_out", "net"]],
        width="stretch",
    )

    if report.account.account_type == AccountType.CREDITCARD:
        render_credit_card_summary(report)

    st.subheader("Monthly Cash Flow")
    st.dataframe(monthly_df, width="stretch")
    st.download_button(
        "Download monthly summary CSV",
        data=dataframe_to_csv_bytes(monthly_df),
        file_name=f"{report.account.account_type.value}_monthly_summary.csv",
        mime="text/csv",
        key=f"monthly-summary:{report.account.storage_key}",
    )

    tab_labels = [
        "Recurring Debits",
        "Variable Recurring Debits",
        "Expense Breakdown",
        "Recurring Credits",
        "Transactions",
        "Insights",
    ]
    if report.account.account_type == AccountType.CREDITCARD:
        tab_labels.insert(4, "Card Details")
    tabs = st.tabs(tab_labels)

    recurring_tab = tabs[0]
    variable_tab = tabs[1]
    breakdown_tab = tabs[2]
    credits_tab = tabs[3]
    card_details_tab = tabs[4] if report.account.account_type == AccountType.CREDITCARD else None
    transactions_tab = tabs[5] if card_details_tab is not None else tabs[4]
    insights_tab = tabs[6] if card_details_tab is not None else tabs[5]

    with recurring_tab:
        render_recurring_candidates(
            title="Recurring Debits",
            candidates=report.recurring_debits,
            scope_key=report.account.storage_key,
            override_store=override_store,
        )

    with variable_tab:
        render_recurring_candidates(
            title="Variable Recurring Debits",
            candidates=report.variable_recurring_debits,
            scope_key=report.account.storage_key,
            override_store=override_store,
        )

    with breakdown_tab:
        render_expense_breakdown(report.recurring_expense_breakdown, report.account.storage_key)

    with credits_tab:
        render_recurring_candidates(
            title="Recurring Credits",
            candidates=report.recurring_credits,
            scope_key=report.account.storage_key,
            override_store=override_store,
        )

    if card_details_tab is not None:
        with card_details_tab:
            render_credit_card_details(report)

    with transactions_tab:
        transaction_df = pd.DataFrame(
            [
                {
                    "date": transaction.date.isoformat(),
                    "amount": str(transaction.amount),
                    "direction": transaction.direction.value,
                    "description": transaction.description_raw,
                    "normalized_description": transaction.description_normalized,
                    "status": transaction.posted_status or "",
                    "source_row": transaction.source_row,
                }
                for transaction in report.transactions
            ]
        )
        st.dataframe(transaction_df, width="stretch")
        st.download_button(
            "Download transactions CSV",
            data=dataframe_to_csv_bytes(transaction_df),
            file_name=f"{report.account.account_type.value}_transactions.csv",
            mime="text/csv",
            key=f"transactions:{report.account.storage_key}",
        )

    with insights_tab:
        insight_metrics = st.columns(3)
        insight_metrics[0].metric(
            "Recurring Monthly Credits",
            format_currency(bundle.recurring_credit_total),
        )
        insight_metrics[1].metric(
            "Fixed Recurring Expenses",
            format_currency(bundle.fixed_recurring_expense_total),
        )
        insight_metrics[2].metric(
            "Variable Recurring Expenses",
            format_currency(bundle.variable_recurring_expense_total),
        )
        for insight in report.insights:
            render_insight(insight.message, insight.evidence, insight.severity.value)


def render_cross_account_dashboard(
    bundle: DashboardBundle,
    override_store: OverrideStore,
) -> None:
    cross_account_report = bundle.report.cross_account_report
    if cross_account_report is None:
        st.info("Upload both a checking and a credit-card CSV to enable cross-account matching.")
        return

    st.subheader("Cross-Account Payment Matches")
    metrics = st.columns(2)
    metrics[0].metric("Matched Card Payments", len(cross_account_report.payment_matches))
    metrics[1].metric(
        "Matched Payment Total",
        format_currency(cross_account_report.matched_payment_total),
    )

    if not cross_account_report.payment_matches:
        st.write("No likely checking-to-credit-card payment matches were detected.")
        return

    payment_df = pd.DataFrame(
        [
            {
                "checking_date": match.checking_transaction.date.isoformat(),
                "checking_amount": str(match.checking_transaction.amount),
                "checking_description": match.checking_transaction.description_raw,
                "card_date": match.credit_card_transaction.date.isoformat(),
                "card_amount": str(match.credit_card_transaction.amount),
                "card_description": match.credit_card_transaction.description_raw,
                "confidence": match.confidence,
                "status": match.status.value,
                "evidence": match.evidence,
            }
            for match in cross_account_report.payment_matches
        ]
    )
    scope_key = build_payment_match_scope_key(
        cross_account_report.checking_account.storage_key,
        cross_account_report.credit_card_account.storage_key,
    )
    st.dataframe(payment_df, width="stretch")
    st.download_button(
        "Download payment match candidates CSV",
        data=dataframe_to_csv_bytes(payment_df),
        file_name="payment_match_candidates.csv",
        mime="text/csv",
        key=f"payment-matches:{scope_key}",
    )
    stored_decisions = get_stored_decisions(PAYMENT_MATCH_NAMESPACE, scope_key, override_store)
    for match in cross_account_report.payment_matches:
        st.write(
            f"{match.checking_transaction.description_normalized} -> "
            f"{match.credit_card_transaction.description_normalized} | "
            f"{format_currency(abs(match.checking_transaction.amount))} / "
            f"{format_currency(match.credit_card_transaction.amount)} | "
            f"confidence {match.confidence}"
        )
        st.selectbox(
            f"Payment match override for {match.match_id}",
            options=[decision.value for decision in OverrideDecision],
            index=list(OverrideDecision).index(
                stored_decisions.get(match.match_id, OverrideDecision.AUTO)
            ),
            key=f"payment_match:{scope_key}:{match.match_id}",
            on_change=handle_payment_match_change,
            args=(scope_key, match.match_id, override_store),
        )


def render_credit_card_summary(report: AccountAnalysisReport) -> None:
    card_metrics = st.columns(4)
    payment_total = sum(
        (transaction.amount for transaction in report.payment_credits),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))
    interest_total = sum(
        (abs(transaction.amount) for transaction in report.interest_transactions),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))
    late_fee_total = sum(
        (abs(transaction.amount) for transaction in report.late_fee_transactions),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))

    card_metrics[0].metric("Card Payments", format_currency(payment_total))
    card_metrics[1].metric("Interest Charges", format_currency(interest_total))
    card_metrics[2].metric("Late Fees", format_currency(late_fee_total))
    if report.interest_estimate is not None and report.interest_estimate.current_apr is not None:
        card_metrics[3].metric(
            "Approx. Current APR",
            f"{report.interest_estimate.current_apr:.2f}%",
        )
    else:
        card_metrics[3].metric("Approx. Current APR", "N/A")

    if report.interest_estimate is not None:
        st.info(
            f"{report.interest_estimate.trend_summary} "
            f"Confidence: {report.interest_estimate.confidence_label}. "
            f"{report.interest_estimate.caveat}"
        )


def render_credit_card_details(report: AccountAnalysisReport) -> None:
    st.markdown("### Credit Card Details")
    detail_rows = pd.DataFrame(
        [
            {
                "date": transaction.date.isoformat(),
                "amount": str(transaction.amount),
                "description": transaction.description_raw,
                "status": transaction.posted_status or "",
            }
            for transaction in (
                tuple(report.payment_credits)
                + tuple(report.interest_transactions)
                + tuple(report.late_fee_transactions)
            )
        ]
    )
    if detail_rows.empty:
        st.write("No card payment, interest, or fee details were detected.")
    else:
        st.dataframe(detail_rows, width="stretch")
        st.download_button(
            "Download credit card detail CSV",
            data=dataframe_to_csv_bytes(detail_rows),
            file_name="credit_card_details.csv",
            mime="text/csv",
            key=f"credit-card-details:{report.account.storage_key}",
        )


def render_recurring_candidates(
    title: str,
    candidates: tuple[RecurringCandidate, ...],
    scope_key: str,
    override_store: OverrideStore,
) -> None:
    widget_scope = title.lower().replace(" ", "_")
    st.markdown(f"### {title}")
    if not candidates:
        st.write("No recurring candidates detected.")
        return
    recurring_df = pd.DataFrame(
        [
            {
                "merchant": candidate.merchant_label,
                "recurring_type": candidate.recurring_type.value,
                "cadence": candidate.cadence,
                "typical_amount": str(candidate.typical_amount),
                "average_amount": str(candidate.amount_average),
                "min_amount": str(candidate.amount_min),
                "max_amount": str(candidate.amount_max),
                "estimated_monthly_amount": str(candidate.estimated_monthly_amount),
                "confidence": candidate.confidence,
                "occurrences": candidate.occurrences,
                "expected_window": candidate.expected_day_window,
            }
            for candidate in candidates
        ]
    )
    st.dataframe(recurring_df, width="stretch")
    st.download_button(
        f"Download {title.lower()} CSV",
        data=dataframe_to_csv_bytes(recurring_df),
        file_name=f"{title.lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key=f"{widget_scope}:download:{scope_key}",
    )
    stored_decisions = get_stored_decisions(RECURRING_NAMESPACE, scope_key, override_store)
    for candidate in candidates:
        current_decision = stored_decisions.get(candidate.candidate_id, OverrideDecision.AUTO)
        st.write(
            f"{candidate.merchant_label}: {candidate.cadence} {candidate.recurring_type.value}, "
            f"{format_currency(candidate.typical_amount)} typical, "
            f"{format_currency(candidate.amount_average)} average, "
            f"confidence {candidate.confidence}"
        )
        st.selectbox(
            f"Override for {candidate.candidate_id}",
            options=[decision.value for decision in OverrideDecision],
            index=list(OverrideDecision).index(current_decision),
            key=f"{widget_scope}:{scope_key}:{candidate.candidate_id}",
            on_change=handle_recurring_override_change,
            args=(scope_key, candidate.candidate_id, override_store, widget_scope),
        )


def handle_recurring_override_change(
    scope_key: str,
    candidate_id: str,
    override_store: OverrideStore,
    widget_scope: str,
) -> None:
    widget_key = f"{widget_scope}:{scope_key}:{candidate_id}"
    selection = OverrideDecision(st.session_state[widget_key])
    override_store.set_decision(scope_key, candidate_id, selection)
    schedule_refresh(RECURRING_NAMESPACE, scope_key, override_store)


def handle_payment_match_change(
    scope_key: str,
    match_id: str,
    override_store: OverrideStore,
) -> None:
    widget_key = f"payment_match:{scope_key}:{match_id}"
    selection = OverrideDecision(st.session_state[widget_key])
    override_store.set_payment_match_decision(scope_key, match_id, selection)
    schedule_refresh(PAYMENT_MATCH_NAMESPACE, scope_key, override_store)


def render_expense_breakdown(
    rows: tuple[RecurringExpenseBreakdownRow, ...],
    scope_key: str,
) -> None:
    st.markdown("### Estimated Monthly Recurring Expense Breakdown")
    if not rows:
        st.write("No recurring expense breakdown is available.")
        return
    breakdown_df = pd.DataFrame(
        [
            {
                "merchant": row.merchant_label,
                "recurring_type": row.recurring_type.value,
                "cadence": row.cadence,
                "estimated_monthly_amount": str(row.estimated_monthly_amount),
                "average_amount": str(row.amount_average),
                "min_amount": str(row.amount_min),
                "max_amount": str(row.amount_max),
                "occurrences": row.occurrences,
                "confidence": row.confidence,
            }
            for row in rows
        ]
    )
    st.dataframe(breakdown_df, width="stretch")
    st.download_button(
        "Download recurring expense breakdown CSV",
        data=dataframe_to_csv_bytes(breakdown_df),
        file_name="recurring_expense_breakdown.csv",
        mime="text/csv",
        key=f"expense-breakdown:{scope_key}",
    )


def render_insight(message: str, evidence: str, severity: str) -> None:
    if severity == InsightSeverity.WARNING.value:
        st.warning(f"{message} {evidence}")
    elif severity == InsightSeverity.POSITIVE.value:
        st.success(f"{message} {evidence}")
    else:
        st.info(f"{message} {evidence}")


def account_heading(report: AccountAnalysisReport) -> str:
    account_label = (
        "Checking Account"
        if report.account.account_type == AccountType.CHECKING
        else "Credit Card"
    )
    return f"{account_label}: {report.account.bank_name} • {report.account.account_number}"


def monthly_dataframe(report: AccountAnalysisReport) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "month": summary.month,
                "total_in": float(summary.total_in),
                "total_out": float(summary.total_out),
                "net": float(summary.net),
            }
            for summary in report.monthly_summaries
        ]
    )


def dataframe_to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    dataframe.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def format_currency(value: Decimal) -> str:
    return f"${value:,.2f}"


def schedule_refresh(namespace: str, scope_key: str, override_store: OverrideStore) -> None:
    st.session_state[refresh_due_key(namespace, scope_key)] = time.time() + REFRESH_DEBOUNCE_SECONDS
    st.session_state[stored_decisions_key(namespace, scope_key)] = get_store_decisions(
        namespace,
        scope_key,
        override_store,
    )


def build_recurring_decision_map(
    checking_parsed: ParsedTransactions | None,
    credit_card_parsed: ParsedTransactions | None,
    override_store: OverrideStore,
) -> dict[str, dict[str, OverrideDecision]]:
    decisions: dict[str, dict[str, OverrideDecision]] = {}
    for parsed in (checking_parsed, credit_card_parsed):
        if parsed is None:
            continue
        decisions[parsed.account.storage_key] = get_applied_decisions(
            RECURRING_NAMESPACE,
            parsed.account.storage_key,
            override_store,
        )
    return decisions


def build_payment_match_decisions(
    checking_parsed: ParsedTransactions | None,
    credit_card_parsed: ParsedTransactions | None,
    override_store: OverrideStore,
) -> dict[str, OverrideDecision]:
    if checking_parsed is None or credit_card_parsed is None:
        return {}
    scope_key = build_payment_match_scope_key(
        checking_parsed.account.storage_key,
        credit_card_parsed.account.storage_key,
    )
    return get_applied_decisions(PAYMENT_MATCH_NAMESPACE, scope_key, override_store)


def collect_pending_refreshes(
    checking_parsed: ParsedTransactions | None,
    credit_card_parsed: ParsedTransactions | None,
    override_store: OverrideStore,
) -> list[tuple[str, str, float]]:
    pending: list[tuple[str, str, float]] = []
    for parsed in (checking_parsed, credit_card_parsed):
        if parsed is None:
            continue
        due_at = apply_pending_refresh_if_due(
            RECURRING_NAMESPACE,
            parsed.account.storage_key,
            override_store,
        )
        if due_at is not None:
            pending.append((RECURRING_NAMESPACE, parsed.account.storage_key, due_at))
    if checking_parsed is not None and credit_card_parsed is not None:
        scope_key = build_payment_match_scope_key(
            checking_parsed.account.storage_key,
            credit_card_parsed.account.storage_key,
        )
        due_at = apply_pending_refresh_if_due(
            PAYMENT_MATCH_NAMESPACE,
            scope_key,
            override_store,
        )
        if due_at is not None:
            pending.append((PAYMENT_MATCH_NAMESPACE, scope_key, due_at))
    return pending


def applied_decisions_key(namespace: str, scope_key: str) -> str:
    return f"applied_decisions:{namespace}:{scope_key}"


def stored_decisions_key(namespace: str, scope_key: str) -> str:
    return f"stored_decisions:{namespace}:{scope_key}"


def refresh_due_key(namespace: str, scope_key: str) -> str:
    return f"refresh_due_at:{namespace}:{scope_key}"


def get_store_decisions(
    namespace: str,
    scope_key: str,
    override_store: OverrideStore,
) -> dict[str, OverrideDecision]:
    if namespace == RECURRING_NAMESPACE:
        return override_store.get_decisions(scope_key)
    return override_store.get_payment_match_decisions(scope_key)


def get_stored_decisions(
    namespace: str,
    scope_key: str,
    override_store: OverrideStore,
) -> dict[str, OverrideDecision]:
    state_key = stored_decisions_key(namespace, scope_key)
    if state_key not in st.session_state:
        st.session_state[state_key] = get_store_decisions(namespace, scope_key, override_store)
    return dict(st.session_state[state_key])


def get_applied_decisions(
    namespace: str,
    scope_key: str,
    override_store: OverrideStore,
) -> dict[str, OverrideDecision]:
    state_key = applied_decisions_key(namespace, scope_key)
    if state_key not in st.session_state:
        st.session_state[state_key] = get_stored_decisions(namespace, scope_key, override_store)
    return dict(st.session_state[state_key])


def apply_pending_refresh_if_due(
    namespace: str,
    scope_key: str,
    override_store: OverrideStore,
) -> float | None:
    due_at = st.session_state.get(refresh_due_key(namespace, scope_key))
    if due_at is None:
        get_stored_decisions(namespace, scope_key, override_store)
        return None
    stored_decisions = get_stored_decisions(namespace, scope_key, override_store)
    if time.time() >= due_at:
        st.session_state[applied_decisions_key(namespace, scope_key)] = stored_decisions
        st.session_state[refresh_due_key(namespace, scope_key)] = None
        return None
    return float(due_at)


@st.fragment(run_every=REFRESH_POLL_INTERVAL)
def render_pending_refresh_notice(
    pending_refreshes: list[tuple[str, str, float]],
) -> None:
    if not pending_refreshes:
        return
    next_due = min(due_at for _, _, due_at in pending_refreshes)
    remaining_seconds = max(0.0, next_due - time.time())
    st.info(
        "Recurring summaries and payment matches will refresh automatically in "
        f"{remaining_seconds:.1f} seconds to batch override updates."
    )
    if remaining_seconds <= 0:
        st.rerun()
