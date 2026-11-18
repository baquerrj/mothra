from __future__ import annotations

import csv
import hashlib
import io
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from spending_visualizer.config import (
    DESCRIPTION_CLEANUP_PATTERNS,
    DESCRIPTION_STRIP_PATTERNS,
    FILENAME_PATTERN,
    MULTISPACE_PATTERN,
    NON_WORD_PATTERN,
    REQUIRED_FILENAME_FORMAT,
    SUPPORTED_ACCOUNT_TYPES,
)
from spending_visualizer.domain.models import AccountDescriptor, AccountType, Direction, Transaction

logger = logging.getLogger(__name__)
ACCOUNT_PART_PATTERN = FILENAME_PATTERN


class IngestionError(ValueError):
    """Raised when the uploaded CSV cannot be parsed safely."""

    def __init__(
        self,
        message: str,
        *,
        reason: str | None = None,
        context: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.context = context or {}


@dataclass(frozen=True)
class ParsedTransactions:
    account: AccountDescriptor
    transactions: tuple[Transaction, ...]


@dataclass(frozen=True)
class FilenameValidationResult:
    filename: str
    bank_name: str | None
    account_type: str | None
    account_number: str | None
    error_reason: str | None

    @property
    def is_valid(self) -> bool:
        return self.error_reason is None


EXPECTED_HEADERS = {"date", "amount", "description"}


def load_transactions(
    file_bytes: bytes,
    filename: str,
    expected_account_type: AccountType | None = None,
) -> ParsedTransactions:
    text = decode_csv(file_bytes)
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise IngestionError("The uploaded CSV is empty.")

    fingerprint = hashlib.sha256(file_bytes).hexdigest()
    account = parse_account_descriptor(filename, fingerprint)
    if expected_account_type is not None and account.account_type != expected_account_type:
        raise IngestionError(
            f"{filename!r} must be uploaded as a {expected_account_type.value} account CSV."
        )

    header_mapping: dict[str, int] | None = detect_header_mapping(rows[0])
    data_rows = rows[1:] if header_mapping is not None else rows
    transactions = tuple(parse_rows(data_rows, header_mapping, account))
    if not transactions:
        raise IngestionError("No valid transactions were found in the uploaded CSV.")

    return ParsedTransactions(account=account, transactions=transactions)


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
        mapping = {name: lowered[name] for name in EXPECTED_HEADERS}
        if "status" in lowered:
            mapping["status"] = lowered["status"]
        return mapping
    return None


def parse_rows(
    rows: Iterable[list[str]],
    header_mapping: dict[str, int] | None,
    account: AccountDescriptor,
) -> Iterable[Transaction]:
    for row_index, row in enumerate(rows, start=2 if header_mapping else 1):
        if not any(cell.strip() for cell in row):
            continue
        date_value, amount_value, description_value, status_value = extract_fields(
            row,
            header_mapping,
        )
        parsed_date = parse_date(date_value, row_index)
        parsed_amount = parse_amount(amount_value, row_index)
        description_raw = description_value.strip()
        if not description_raw:
            raise IngestionError(f"Row {row_index} is missing a transaction description.")
        yield Transaction(
            account=account,
            date=parsed_date,
            amount=parsed_amount,
            description_raw=description_raw,
            description_normalized=normalize_description(description_raw),
            direction=Direction.CREDIT if parsed_amount >= Decimal("0.00") else Direction.DEBIT,
            source_row=row_index,
            posted_status=(
                status_value.strip()
                if status_value is not None and status_value.strip()
                else None
            ),
        )


def extract_fields(
    row: list[str],
    header_mapping: dict[str, int] | None,
) -> tuple[str, str, str, str | None]:
    if header_mapping is not None:
        return (
            row[header_mapping["date"]],
            row[header_mapping["amount"]],
            row[header_mapping["description"]],
            row[header_mapping["status"]] if "status" in header_mapping else None,
        )
    if len(row) >= 5:
        return row[0], row[1], row[4], None
    if len(row) >= 3:
        return row[0], row[1], row[2], None
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


def parse_account_descriptor(filename: str, fingerprint: str) -> AccountDescriptor:
    validation = validate_account_filename(filename)
    if not validation.is_valid:
        message = build_filename_error_message(validation)
        logger.warning(
            "Filename validation failed: filename=%s reason=%s expected_format=%s",
            validation.filename,
            validation.error_reason,
            REQUIRED_FILENAME_FORMAT,
        )
        raise IngestionError(
            message,
            reason=validation.error_reason,
            context={
                "filename": validation.filename,
                "expected_format": REQUIRED_FILENAME_FORMAT,
            },
        )
    match = FILENAME_PATTERN.match(validation.filename)
    assert match is not None
    return AccountDescriptor(
        source_filename=validation.filename,
        bank_name=match.group("bank"),
        account_type=AccountType(match.group("account_type").lower()),
        account_number=match.group("account_number"),
        fingerprint=fingerprint,
    )


def validate_account_filename(filename: str) -> FilenameValidationResult:
    cleaned = filename.strip()
    lowered = cleaned.lower()
    if not lowered.endswith(".csv"):
        return FilenameValidationResult(
            filename=cleaned,
            bank_name=None,
            account_type=None,
            account_number=None,
            error_reason="expected a .csv extension",
        )

    stem = cleaned[:-4]
    if "__" not in stem:
        reason = "found single underscores instead of required '__' separators"
        if "_" not in stem:
            reason = "missing required '__' separators"
        return FilenameValidationResult(
            filename=cleaned,
            bank_name=None,
            account_type=None,
            account_number=None,
            error_reason=reason,
        )

    parts = stem.split("__")
    if len(parts) != 3:
        return FilenameValidationResult(
            filename=cleaned,
            bank_name=None,
            account_type=None,
            account_number=None,
            error_reason="expected exactly three filename segments separated by '__'",
        )

    bank_name, account_type, account_number = parts
    if not bank_name:
        return FilenameValidationResult(
            filename=cleaned,
            bank_name=None,
            account_type=account_type or None,
            account_number=account_number or None,
            error_reason="missing bank segment before the first '__'",
        )
    if not account_type:
        return FilenameValidationResult(
            filename=cleaned,
            bank_name=bank_name,
            account_type=None,
            account_number=account_number or None,
            error_reason="missing account_type segment between '__' separators",
        )
    if account_type.lower() not in SUPPORTED_ACCOUNT_TYPES:
        return FilenameValidationResult(
            filename=cleaned,
            bank_name=bank_name,
            account_type=account_type,
            account_number=account_number or None,
            error_reason=(
                f"unsupported account_type {account_type!r}; use checking or creditcard"
            ),
        )
    if not account_number:
        return FilenameValidationResult(
            filename=cleaned,
            bank_name=bank_name,
            account_type=account_type,
            account_number=None,
            error_reason="missing account_number segment after the last '__'",
        )
    if FILENAME_PATTERN.match(cleaned) is None:
        return FilenameValidationResult(
            filename=cleaned,
            bank_name=bank_name,
            account_type=account_type,
            account_number=account_number,
            error_reason=(
                "bank and account_number may only contain letters, numbers, and hyphens"
            ),
        )
    return FilenameValidationResult(
        filename=cleaned,
        bank_name=bank_name,
        account_type=account_type,
        account_number=account_number,
        error_reason=None,
    )


def build_filename_error_message(validation: FilenameValidationResult) -> str:
    assert validation.error_reason is not None
    return (
        f"Invalid filename {validation.filename!r}: expected {REQUIRED_FILENAME_FORMAT}; "
        f"{validation.error_reason}."
    )
