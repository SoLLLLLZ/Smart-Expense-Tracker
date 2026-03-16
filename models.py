from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from config import VALID_CATEGORIES, VALID_PAYMENT_METHODS, DATE_FORMAT


@dataclass
class Expense:
    date: date
    merchant: str
    amount: float
    category: str
    payment_method: str
    source: str  # "manual" or "ocr"
    id: Optional[int] = None
    created_at: Optional[str] = None

    def validate(self) -> list:
        """Returns a list of error strings. Empty list means valid."""
        errors = []

        if not self.merchant or not self.merchant.strip():
            errors.append("Merchant name cannot be empty.")

        if not isinstance(self.amount, (int, float)) or self.amount <= 0:
            errors.append("Amount must be a positive number.")

        if self.category not in VALID_CATEGORIES:
            errors.append(
                f"Invalid category '{self.category}'. "
                f"Valid options: {', '.join(VALID_CATEGORIES)}"
            )

        if self.payment_method not in VALID_PAYMENT_METHODS:
            errors.append(
                f"Invalid payment method '{self.payment_method}'. "
                f"Valid options: {', '.join(VALID_PAYMENT_METHODS)}"
            )

        if self.source not in ("manual", "ocr"):
            errors.append("Source must be 'manual' or 'ocr'.")

        if not isinstance(self.date, date):
            errors.append("Date must be a datetime.date object.")

        return errors

    def to_dict(self) -> dict:
        """Serialize to a plain dict for display or storage."""
        return {
            "id": self.id,
            "date": self.date.strftime(DATE_FORMAT) if isinstance(self.date, date) else self.date,
            "merchant": self.merchant,
            "amount": self.amount,
            "category": self.category,
            "payment_method": self.payment_method,
            "source": self.source,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "Expense":
        """Construct an Expense from a raw sqlite3 row tuple.

        Expected column order: id, date, merchant, amount, category,
        payment_method, source, created_at
        """
        expense_id, date_str, merchant, amount, category, payment_method, source, created_at = row
        parsed_date = datetime.strptime(date_str, DATE_FORMAT).date()
        return cls(
            id=expense_id,
            date=parsed_date,
            merchant=merchant,
            amount=amount,
            category=category,
            payment_method=payment_method,
            source=source,
            created_at=created_at,
        )
