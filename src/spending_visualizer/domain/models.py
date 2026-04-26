from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class Direction(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


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
class Transaction:
    date: date
    amount: Decimal
    description_raw: str
    description_normalized: str
    direction: Direction
    source_row: int


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
class AnalysisReport:
    fingerprint: str
    transactions: tuple[Transaction, ...]
    monthly_summaries: tuple[MonthlySummary, ...]
    recurring_debits: tuple[RecurringCandidate, ...]
    variable_recurring_debits: tuple[RecurringCandidate, ...]
    recurring_credits: tuple[RecurringCandidate, ...]
    recurring_expense_breakdown: tuple[RecurringExpenseBreakdownRow, ...]
    insights: tuple[Insight, ...]
