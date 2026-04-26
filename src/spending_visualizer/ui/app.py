from __future__ import annotations

import io
import time
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

from spending_visualizer.application.services import (
    ReportBundle,
    build_report_from_parsed,
)
from spending_visualizer.domain.models import (
    InsightSeverity,
    OverrideDecision,
    RecurringCandidate,
    RecurringExpenseBreakdownRow,
)
from spending_visualizer.ingest.csv_loader import IngestionError, load_transactions
from spending_visualizer.persistence.overrides import OverrideStore

REFRESH_DEBOUNCE_SECONDS = 3.0
REFRESH_POLL_INTERVAL = "1s"


def main() -> None:
    st.set_page_config(page_title="Spending Visualizer", layout="wide")
    st.title("Spending Visualizer")
    st.caption("Local-only checking account analysis with recurring payment detection.")

    override_store = OverrideStore()
    uploaded_file = st.file_uploader("Upload a checking account CSV", type=["csv"])
    sample_button = st.button("Load bundled sample CSV")

    file_bytes: bytes | None = None
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
    elif sample_button:
        file_bytes = Path("Checking1.csv").read_bytes()

    if file_bytes is None:
        st.info("Upload a CSV to begin. Data stays on this machine.")
        return

    try:
        parsed = load_transactions(file_bytes)
        pending_info = apply_pending_refresh_if_due(parsed.fingerprint, override_store)
        applied_decisions = get_applied_decisions(parsed.fingerprint, override_store)
        bundle = build_report_from_parsed(parsed, applied_decisions)
    except IngestionError as exc:
        st.error(str(exc))
        return

    render_pending_refresh_notice(parsed.fingerprint, pending_info)
    render_dashboard(bundle, override_store)


def render_dashboard(bundle: ReportBundle, override_store: OverrideStore) -> None:
    report = bundle.report
    monthly_df = monthly_dataframe(bundle)

    st.subheader("Overview")
    metrics = st.columns(5)
    total_in = sum((summary.total_in for summary in report.monthly_summaries), Decimal("0.00"))
    total_out = sum((summary.total_out for summary in report.monthly_summaries), Decimal("0.00"))
    metrics[0].metric("Months", len(report.monthly_summaries))
    metrics[1].metric("Total In", format_currency(total_in))
    metrics[2].metric("Total Out", format_currency(total_out))
    metrics[3].metric("Recurring Monthly Expenses", format_currency(bundle.recurring_expense_total))
    metrics[4].metric(
        "Variable Recurring Expenses",
        format_currency(bundle.variable_recurring_expense_total),
    )

    st.line_chart(
        monthly_df.set_index("month")[["total_in", "total_out", "net"]],
        width="stretch",
    )

    st.subheader("Monthly Cash Flow")
    st.dataframe(monthly_df, width="stretch")
    st.download_button(
        "Download monthly summary CSV",
        data=dataframe_to_csv_bytes(monthly_df),
        file_name="monthly_summary.csv",
        mime="text/csv",
    )

    tabs = st.tabs(
        [
            "Recurring Debits",
            "Variable Recurring Debits",
            "Expense Breakdown",
            "Recurring Credits",
            "Transactions",
            "Insights",
        ]
    )
    recurring_tab, variable_tab, breakdown_tab, credits_tab, transactions_tab, insights_tab = tabs

    with recurring_tab:
        render_recurring_candidates(
            title="Recurring Debits",
            candidates=report.recurring_debits,
            fingerprint=report.fingerprint,
            override_store=override_store,
        )

    with variable_tab:
        render_recurring_candidates(
            title="Variable Recurring Debits",
            candidates=report.variable_recurring_debits,
            fingerprint=report.fingerprint,
            override_store=override_store,
        )

    with breakdown_tab:
        render_expense_breakdown(report.recurring_expense_breakdown)

    with credits_tab:
        render_recurring_candidates(
            title="Recurring Credits",
            candidates=report.recurring_credits,
            fingerprint=report.fingerprint,
            override_store=override_store,
        )

    with transactions_tab:
        transaction_df = pd.DataFrame(
            [
                {
                    "date": transaction.date.isoformat(),
                    "amount": str(transaction.amount),
                    "direction": transaction.direction.value,
                    "description": transaction.description_raw,
                    "normalized_description": transaction.description_normalized,
                    "source_row": transaction.source_row,
                }
                for transaction in report.transactions
            ]
        )
        st.dataframe(transaction_df, width="stretch")
        st.download_button(
            "Download transactions CSV",
            data=dataframe_to_csv_bytes(transaction_df),
            file_name="transactions.csv",
            mime="text/csv",
        )

    with insights_tab:
        metrics = st.columns(3)
        metrics[0].metric(
            "Recurring Monthly Credits",
            format_currency(bundle.recurring_credit_total),
        )
        metrics[1].metric(
            "Fixed Recurring Expenses",
            format_currency(bundle.fixed_recurring_expense_total),
        )
        metrics[2].metric(
            "Variable Recurring Expenses",
            format_currency(bundle.variable_recurring_expense_total),
        )
        for insight in report.insights:
            render_insight(insight.message, insight.evidence, insight.severity.value)


def render_recurring_candidates(
    title: str,
    candidates: tuple[RecurringCandidate, ...],
    fingerprint: str,
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
    )
    for candidate in candidates:
        current_decision = get_stored_decisions(fingerprint, override_store).get(
            candidate.candidate_id,
            OverrideDecision.AUTO,
        )
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
            key=f"{widget_scope}:{fingerprint}:{candidate.candidate_id}",
            on_change=handle_override_change,
            args=(fingerprint, candidate.candidate_id, override_store, widget_scope),
        )


def handle_override_change(
    fingerprint: str,
    candidate_id: str,
    override_store: OverrideStore,
    widget_scope: str,
) -> None:
    widget_key = f"{widget_scope}:{fingerprint}:{candidate_id}"
    selection = OverrideDecision(st.session_state[widget_key])
    override_store.set_decision(
        fingerprint=fingerprint,
        candidate_id=candidate_id,
        decision=selection,
    )
    st.session_state[refresh_due_key(fingerprint)] = time.time() + REFRESH_DEBOUNCE_SECONDS
    st.session_state[stored_decisions_key(fingerprint)] = override_store.get_decisions(fingerprint)


def render_expense_breakdown(rows: tuple[RecurringExpenseBreakdownRow, ...]) -> None:
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
    )


def render_insight(message: str, evidence: str, severity: str) -> None:
    if severity == InsightSeverity.WARNING.value:
        st.warning(f"{message} {evidence}")
    elif severity == InsightSeverity.POSITIVE.value:
        st.success(f"{message} {evidence}")
    else:
        st.info(f"{message} {evidence}")


def monthly_dataframe(bundle: ReportBundle) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "month": summary.month,
                "total_in": float(summary.total_in),
                "total_out": float(summary.total_out),
                "net": float(summary.net),
            }
            for summary in bundle.report.monthly_summaries
        ]
    )


def dataframe_to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    dataframe.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def format_currency(value: Decimal) -> str:
    return f"${value:,.2f}"


def applied_decisions_key(fingerprint: str) -> str:
    return f"applied_decisions:{fingerprint}"


def stored_decisions_key(fingerprint: str) -> str:
    return f"stored_decisions:{fingerprint}"


def refresh_due_key(fingerprint: str) -> str:
    return f"refresh_due_at:{fingerprint}"


def get_stored_decisions(
    fingerprint: str,
    override_store: OverrideStore,
) -> dict[str, OverrideDecision]:
    state_key = stored_decisions_key(fingerprint)
    if state_key not in st.session_state:
        st.session_state[state_key] = override_store.get_decisions(fingerprint)
    return dict(st.session_state[state_key])


def get_applied_decisions(
    fingerprint: str,
    override_store: OverrideStore,
) -> dict[str, OverrideDecision]:
    state_key = applied_decisions_key(fingerprint)
    if state_key not in st.session_state:
        st.session_state[state_key] = get_stored_decisions(fingerprint, override_store)
    return dict(st.session_state[state_key])


def apply_pending_refresh_if_due(
    fingerprint: str,
    override_store: OverrideStore,
) -> float | None:
    due_at = st.session_state.get(refresh_due_key(fingerprint))
    if due_at is None:
        get_stored_decisions(fingerprint, override_store)
        return None
    stored_decisions = get_stored_decisions(fingerprint, override_store)
    if time.time() >= due_at:
        st.session_state[applied_decisions_key(fingerprint)] = stored_decisions
        st.session_state[refresh_due_key(fingerprint)] = None
        return None
    return float(due_at)


@st.fragment(run_every=REFRESH_POLL_INTERVAL)
def render_pending_refresh_notice(
    fingerprint: str,
    due_at: float | None,
) -> None:
    if due_at is None:
        return
    remaining_seconds = max(0.0, due_at - time.time())
    st.info(
        "Recurring summaries will refresh automatically in "
        f"{remaining_seconds:.1f} seconds to batch override updates."
    )
    if remaining_seconds <= 0:
        st.rerun()
