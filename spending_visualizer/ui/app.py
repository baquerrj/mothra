from __future__ import annotations

import io
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

from spending_visualizer.application.services import ReportBundle, build_report
from spending_visualizer.domain.models import (
    InsightSeverity,
    OverrideDecision,
    RecurringCandidate,
)
from spending_visualizer.ingest.csv_loader import IngestionError
from spending_visualizer.persistence.overrides import OverrideStore


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
        bundle = build_report(file_bytes, override_store)
    except IngestionError as exc:
        st.error(str(exc))
        return

    render_dashboard(bundle, override_store)


def render_dashboard(bundle: ReportBundle, override_store: OverrideStore) -> None:
    report = bundle.report
    monthly_df = monthly_dataframe(bundle)

    st.subheader("Overview")
    metrics = st.columns(4)
    total_in = sum((summary.total_in for summary in report.monthly_summaries), Decimal("0.00"))
    total_out = sum((summary.total_out for summary in report.monthly_summaries), Decimal("0.00"))
    metrics[0].metric("Months", len(report.monthly_summaries))
    metrics[1].metric("Total In", format_currency(total_in))
    metrics[2].metric("Total Out", format_currency(total_out))
    metrics[3].metric("Recurring Monthly Expenses", format_currency(bundle.recurring_expense_total))

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

    recurring_tab, credits_tab, transactions_tab, insights_tab = st.tabs(
        ["Recurring Debits", "Recurring Credits", "Transactions", "Insights"]
    )

    with recurring_tab:
        render_recurring_candidates(
            title="Recurring Debits",
            candidates=report.recurring_debits,
            fingerprint=report.fingerprint,
            override_store=override_store,
        )

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
        st.metric("Recurring Monthly Credits", format_currency(bundle.recurring_credit_total))
        for insight in report.insights:
            render_insight(insight.message, insight.evidence, insight.severity.value)


def render_recurring_candidates(
    title: str,
    candidates: tuple[RecurringCandidate, ...],
    fingerprint: str,
    override_store: OverrideStore,
) -> None:
    st.markdown(f"### {title}")
    if not candidates:
        st.write("No recurring candidates detected.")
        return
    recurring_df = pd.DataFrame(
        [
            {
                "merchant": candidate.merchant_label,
                "cadence": candidate.cadence,
                "typical_amount": str(candidate.typical_amount),
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
        current_decision = override_store.get_decisions(fingerprint).get(
            candidate.candidate_id,
            OverrideDecision.AUTO,
        )
        st.write(
            f"{candidate.merchant_label}: {candidate.cadence}, "
            f"{format_currency(candidate.typical_amount)} typical, "
            f"confidence {candidate.confidence}"
        )
        selection = st.selectbox(
            f"Override for {candidate.candidate_id}",
            options=[decision.value for decision in OverrideDecision],
            index=list(OverrideDecision).index(current_decision),
            key=f"{fingerprint}:{candidate.candidate_id}",
        )
        override_store.set_decision(
            fingerprint=fingerprint,
            candidate_id=candidate.candidate_id,
            decision=OverrideDecision(selection),
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
