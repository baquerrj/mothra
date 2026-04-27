import os
import re
from dataclasses import dataclass
from pathlib import Path

FILENAME_PATTERN = re.compile(
    r"^(?P<bank>[A-Za-z0-9-]+)__(?P<account_type>checking|creditcard)__(?P<account_number>[A-Za-z0-9-]+)\.csv$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CadenceRule:
    name: str
    interval_days: int
    tolerance_days: int
    annual_occurrences: int


@dataclass(frozen=True)
class AnalysisConfig:
    minimum_occurrences: int = 3
    minimum_confidence: float = 0.55
    fixed_amount_match_ratio: float = 0.65
    amount_variance_ratio: float = 0.15
    amount_variance_floor: float = 5.0
    variable_amount_ratio_floor: float = 0.20
    variable_min_unique_amounts: int = 3
    payment_match_window_days: int = 5
    payment_match_min_confidence: float = 0.60
    recent_interest_months: int = 3
    cadence_rules: tuple[CadenceRule, ...] = (
        CadenceRule("weekly", 7, 2, 52),
        CadenceRule("biweekly", 14, 3, 26),
        CadenceRule("monthly", 30, 5, 12),
    )


DESCRIPTION_CLEANUP_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^PURCHASE AUTHORIZED ON \d{2}/\d{2}\s+", re.IGNORECASE),
    re.compile(r"^RECURRING PAYMENT AUTHORIZED ON \d{2}/\d{2}\s+", re.IGNORECASE),
    re.compile(r"^NON-WF ATM WITHDRAWAL AUTHORIZED ON \d{2}/\d{2}\s+", re.IGNORECASE),
    re.compile(r"^ONLINE TRANSFER (FROM|TO)\s+", re.IGNORECASE),
)

DESCRIPTION_STRIP_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bCARD\s+\d+\b.*", re.IGNORECASE),
    re.compile(r"\bREF\s*#?\s*[A-Z0-9-]+\b.*", re.IGNORECASE),
    re.compile(r"\bORDER\s*#?\s*[A-Z0-9-]+\b.*", re.IGNORECASE),
    re.compile(r"\bS\d+\b.*", re.IGNORECASE),
    re.compile(r"\bP\d+\b.*", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{3}-\d{4}\b.*", re.IGNORECASE),
)

NON_WORD_PATTERN = re.compile(r"[^A-Z ]+")
MULTISPACE_PATTERN = re.compile(r"\s+")

REQUIREMENT_IDS: tuple[str, ...] = (
    "SYS-01",
    "SYS-02",
    "SYS-03",
    "SYS-04",
    "SYS-05",
    "SYS-06",
    "SYS-07",
    "SYS-08",
    "SYS-09",
    "SYS-10",
    "SYS-11",
    "SYS-12",
    "SYS-13",
    "SYS-14",
    "SYS-15",
    "ING-01",
    "ING-02",
    "ING-03",
    "ING-04",
    "ANL-01",
    "ANL-02",
    "ANL-03",
    "ANL-04",
    "ANL-05",
    "ANL-06",
    "ANL-07",
    "UI-01",
    "UI-02",
    "UI-03",
    "UI-04",
    "UI-05",
    "PST-01",
    "PST-02",
    "PST-03",
    "QLT-01",
    "QLT-02",
    "ARC-01",
    "ARC-02",
    "ARC-03",
    "ARC-04",
    "ARC-05",
    "ARC-06",
    "DSN-01",
    "DSN-02",
    "DSN-03",
    "DSN-04",
    "DSN-05",
)


def default_override_path() -> Path:
    root = os.environ.get("SPENDING_VISUALIZER_OVERRIDE_DIR")
    if root:
        return Path(root).expanduser() / "overrides.json"
    return Path.home() / ".simple_account_viewer" / "overrides.json"
