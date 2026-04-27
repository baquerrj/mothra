from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class Direction(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class AccountType(str, Enum):
    CHECKING = "checking"
    CREDITCARD = "creditcard"


class InsightSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    POSITIVE = "positive"


class OverrideDecision(str, Enum):
    AUTO = "auto"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class RecurringType(str, Enum):
    FIXED = "fixed"
    VARIABLE = "variable"


@dataclass(frozen=True)
class AccountDescriptor:
    source_filename: str
    bank_name: str
    account_type: AccountType
    account_number: str
    fingerprint: str

    @property
    def storage_key(self) -> str:
        return (
            f"{self.bank_name.lower()}:{self.account_type.value}:"
            f"{self.account_number}:{self.fingerprint}"
        )


@dataclass(frozen=True)
class Transaction:
    account: AccountDescriptor
    date: date
    amount: Decimal
    description_raw: str
    description_normalized: str
    direction: Direction
    source_row: int
    posted_status: str | None = None


@dataclass(frozen=True)
class RecurringCandidate:
    candidate_id: str
    kind: Direction
    fingerprint: str
    merchant_label: str
    recurring_type: RecurringType
    cadence: str
    expected_day_window: str
    typical_amount: Decimal
    amount_average: Decimal
    amount_min: Decimal
    amount_max: Decimal
    amount_tolerance: Decimal
    occurrences: int
    confidence: float
    estimated_monthly_amount: Decimal
    transactions: tuple[Transaction, ...]


@dataclass(frozen=True)
class MonthlySummary:
    month: str
    total_in: Decimal
    total_out: Decimal
    net: Decimal


@dataclass(frozen=True)
class Insight:
    insight_type: str
    severity: InsightSeverity
    message: str
    evidence: str


@dataclass(frozen=True)
class InterestEstimate:
    current_apr: Decimal | None
    recent_average_apr: Decimal | None
    recent_interest_average: Decimal
    confidence_label: str
    trend_summary: str
    caveat: str


@dataclass(frozen=True)
class RecurringExpenseBreakdownRow:
    merchant_label: str
    cadence: str
    recurring_type: RecurringType
    estimated_monthly_amount: Decimal
    amount_average: Decimal
    amount_min: Decimal
    amount_max: Decimal
    occurrences: int
    confidence: float


@dataclass(frozen=True)
class PaymentMatchCandidate:
    match_id: str
    checking_transaction: Transaction
    credit_card_transaction: Transaction
    confidence: float
    evidence: str
    status: OverrideDecision


@dataclass(frozen=True)
class AccountAnalysisReport:
    account: AccountDescriptor
    transactions: tuple[Transaction, ...]
    monthly_summaries: tuple[MonthlySummary, ...]
    recurring_debits: tuple[RecurringCandidate, ...]
    variable_recurring_debits: tuple[RecurringCandidate, ...]
    recurring_credits: tuple[RecurringCandidate, ...]
    recurring_expense_breakdown: tuple[RecurringExpenseBreakdownRow, ...]
    insights: tuple[Insight, ...]
    payment_credits: tuple[Transaction, ...] = ()
    interest_transactions: tuple[Transaction, ...] = ()
    late_fee_transactions: tuple[Transaction, ...] = ()
    interest_estimate: InterestEstimate | None = None


@dataclass(frozen=True)
class CrossAccountReport:
    checking_account: AccountDescriptor
    credit_card_account: AccountDescriptor
    payment_matches: tuple[PaymentMatchCandidate, ...]
    matched_payment_total: Decimal


@dataclass(frozen=True)
class DashboardReport:
    checking_report: AccountAnalysisReport | None
    credit_card_report: AccountAnalysisReport | None
    cross_account_report: CrossAccountReport | None
