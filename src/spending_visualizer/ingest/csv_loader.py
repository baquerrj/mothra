from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from spending_visualizer.config import (
    DESCRIPTION_CLEANUP_PATTERNS,
    DESCRIPTION_STRIP_PATTERNS,
    MULTISPACE_PATTERN,
    NON_WORD_PATTERN,
)
from spending_visualizer.domain.models import Direction, Transaction


class IngestionError(ValueError):
    """Raised when the uploaded CSV cannot be parsed safely."""


@dataclass(frozen=True)
class ParsedTransactions:
    fingerprint: str
    transactions: tuple[Transaction, ...]


EXPECTED_HEADERS = {"date", "amount", "description"}


def load_transactions(file_bytes: bytes) -> ParsedTransactions:
    text = decode_csv(file_bytes)
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise IngestionError("The uploaded CSV is empty.")

    header_mapping: dict[str, int] | None = detect_header_mapping(rows[0])
    data_rows = rows[1:] if header_mapping is not None else rows
    transactions = tuple(parse_rows(data_rows, header_mapping))
    if not transactions:
        raise IngestionError("No valid transactions were found in the uploaded CSV.")

    fingerprint = hashlib.sha256(file_bytes).hexdigest()
    return ParsedTransactions(fingerprint=fingerprint, transactions=transactions)


def decode_csv(file_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise IngestionError(
        "The file encoding is not supported. Use UTF-8 or a standard bank-export CSV."
    )


def detect_header_mapping(first_row: list[str]) -> dict[str, int] | None:
    lowered = {cell.strip().strip('"').lower(): idx for idx, cell in enumerate(first_row)}
    if EXPECTED_HEADERS.issubset(lowered):
        return {name: lowered[name] for name in EXPECTED_HEADERS}
    return None


def parse_rows(
    rows: Iterable[list[str]],
    header_mapping: dict[str, int] | None,
) -> Iterable[Transaction]:
    for row_index, row in enumerate(rows, start=2 if header_mapping else 1):
        if not any(cell.strip() for cell in row):
            continue
        date_value, amount_value, description_value = extract_fields(row, header_mapping)
        parsed_date = parse_date(date_value, row_index)
        parsed_amount = parse_amount(amount_value, row_index)
        description_raw = description_value.strip()
        if not description_raw:
            raise IngestionError(f"Row {row_index} is missing a transaction description.")
        yield Transaction(
            date=parsed_date,
            amount=parsed_amount,
            description_raw=description_raw,
            description_normalized=normalize_description(description_raw),
            direction=Direction.CREDIT if parsed_amount >= Decimal("0.00") else Direction.DEBIT,
            source_row=row_index,
        )


def extract_fields(row: list[str], header_mapping: dict[str, int] | None) -> tuple[str, str, str]:
    if header_mapping is not None:
        return (
            row[header_mapping["date"]],
            row[header_mapping["amount"]],
            row[header_mapping["description"]],
        )
    if len(row) >= 5:
        return row[0], row[1], row[4]
    if len(row) >= 3:
        return row[0], row[1], row[2]
    raise IngestionError(
        "The uploaded CSV must contain logical Date, Amount, and Description fields."
    )


def parse_date(value: str, row_index: int) -> date:
    cleaned = value.strip().strip('"')
    for date_format in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, date_format).date()
        except ValueError:
            continue
    raise IngestionError(f"Row {row_index} has an invalid date value: {value!r}")


def parse_amount(value: str, row_index: int) -> Decimal:
    cleaned = value.strip().strip('"').replace(",", "")
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise IngestionError(f"Row {row_index} has an invalid amount value: {value!r}") from exc


def normalize_description(description: str) -> str:
    cleaned = description.strip().upper()
    for pattern in DESCRIPTION_CLEANUP_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    for pattern in DESCRIPTION_STRIP_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    cleaned = NON_WORD_PATTERN.sub(" ", cleaned)
    cleaned = MULTISPACE_PATTERN.sub(" ", cleaned).strip()
    return cleaned or "UNKNOWN TRANSACTION"
