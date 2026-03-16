"""Analytics functions for the Smart Expense Tracker.

All functions are pure — they operate on a list[Expense] and have no
database access. The caller is responsible for fetching data via crud.py
and passing it here.
"""
from collections import defaultdict
from datetime import date
from typing import Optional

from models import Expense


def total_spending(expenses: list) -> float:
    """Sum all amounts. Returns 0.0 for an empty list."""
    return round(sum(e.amount for e in expenses), 2)


def spending_by_category(expenses: list) -> dict:
    """Return {category: total_amount} sorted descending by amount."""
    totals = defaultdict(float)
    for e in expenses:
        totals[e.category] += e.amount
    return dict(
        sorted(totals.items(), key=lambda x: x[1], reverse=True)
    )


def spending_by_merchant(expenses: list) -> dict:
    """Return {merchant: total_amount} sorted descending by amount."""
    totals = defaultdict(float)
    for e in expenses:
        totals[e.merchant] += e.amount
    return dict(
        sorted(totals.items(), key=lambda x: x[1], reverse=True)
    )


def spending_by_payment_method(expenses: list) -> dict:
    """Return {payment_method: total_amount} sorted descending by amount."""
    totals = defaultdict(float)
    for e in expenses:
        totals[e.payment_method] += e.amount
    return dict(
        sorted(totals.items(), key=lambda x: x[1], reverse=True)
    )


def monthly_summary(expenses: list) -> dict:
    """Return {'YYYY-MM': total_amount} sorted chronologically."""
    totals = defaultdict(float)
    for e in expenses:
        if e.date is None:
            continue
        key = e.date.strftime("%Y-%m")
        totals[key] += e.amount
    return dict(sorted(totals.items()))


def top_merchants(expenses: list, n: int = 5) -> list:
    """Return top-n merchants by total spend as [(merchant, amount)] tuples."""
    by_merchant = spending_by_merchant(expenses)
    return list(by_merchant.items())[:n]


def format_report(expenses: list, title: str = "Expense Report") -> str:
    """Render a multi-section human-readable report string."""
    if not expenses:
        return f"-- {title} --\n\nNo expenses to report."

    lines = []
    lines.append(f"{'=' * 50}")
    lines.append(f"  {title}")
    lines.append(f"{'=' * 50}")

    # Total
    total = total_spending(expenses)
    lines.append(f"\n  Total Spending: ${total:.2f}")
    lines.append(f"  Records:        {len(expenses)}")

    # By category
    lines.append(f"\n  {'--- By Category ' + '-' * 33}")
    by_cat = spending_by_category(expenses)
    for cat, amt in by_cat.items():
        pct = (amt / total * 100) if total else 0
        lines.append(f"  {cat:<20}  ${amt:>8.2f}  ({pct:.1f}%)")

    # By payment method
    lines.append(f"\n  {'--- By Payment Method ' + '-' * 28}")
    by_pay = spending_by_payment_method(expenses)
    for method, amt in by_pay.items():
        lines.append(f"  {method:<20}  ${amt:>8.2f}")

    # Monthly summary
    monthly = monthly_summary(expenses)
    if monthly:
        lines.append(f"\n  {'--- Monthly Summary ' + '-' * 30}")
        for month, amt in monthly.items():
            lines.append(f"  {month:<20}  ${amt:>8.2f}")

    # Top merchants
    top = top_merchants(expenses, n=5)
    if top:
        lines.append(f"\n  {'--- Top Merchants ' + '-' * 31}")
        for i, (merchant, amt) in enumerate(top, 1):
            lines.append(f"  {i}. {merchant:<18}  ${amt:>8.2f}")

    lines.append(f"\n{'=' * 50}")
    return "\n".join(lines)
