"""Tests for analytics.py using known fixture data."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from models import Expense
from analytics import (
    total_spending,
    spending_by_category,
    spending_by_merchant,
    spending_by_payment_method,
    monthly_summary,
    top_merchants,
    format_report,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_expense(**kwargs) -> Expense:
    defaults = dict(
        date=date(2026, 3, 1),
        merchant="Starbucks",
        amount=10.00,
        category="Food & Dining",
        payment_method="credit_card",
        source="manual",
        id=1,
    )
    defaults.update(kwargs)
    return Expense(**defaults)


SAMPLE_EXPENSES = [
    make_expense(id=1, merchant="Starbucks",  amount=6.75,  category="Food & Dining",   payment_method="credit_card",  date=date(2026, 1, 5)),
    make_expense(id=2, merchant="Uber",        amount=14.20, category="Transportation",  payment_method="debit_card",   date=date(2026, 1, 15)),
    make_expense(id=3, merchant="Chipotle",    amount=12.50, category="Food & Dining",   payment_method="cash",         date=date(2026, 2, 3)),
    make_expense(id=4, merchant="Amazon",      amount=49.99, category="Shopping",        payment_method="credit_card",  date=date(2026, 2, 20)),
    make_expense(id=5, merchant="Starbucks",   amount=5.25,  category="Food & Dining",   payment_method="mobile_payment", date=date(2026, 3, 10)),
]


# ---------------------------------------------------------------------------
# total_spending
# ---------------------------------------------------------------------------

def test_total_spending_correct():
    total = total_spending(SAMPLE_EXPENSES)
    assert total == round(6.75 + 14.20 + 12.50 + 49.99 + 5.25, 2)


def test_total_spending_empty_list():
    assert total_spending([]) == 0.0


def test_total_spending_single():
    assert total_spending([make_expense(amount=42.00)]) == 42.00


# ---------------------------------------------------------------------------
# spending_by_category
# ---------------------------------------------------------------------------

def test_spending_by_category_keys():
    result = spending_by_category(SAMPLE_EXPENSES)
    assert set(result.keys()) == {"Food & Dining", "Transportation", "Shopping"}


def test_spending_by_category_food_total():
    result = spending_by_category(SAMPLE_EXPENSES)
    assert result["Food & Dining"] == round(6.75 + 12.50 + 5.25, 2)


def test_spending_by_category_sorted_descending():
    result = spending_by_category(SAMPLE_EXPENSES)
    amounts = list(result.values())
    assert amounts == sorted(amounts, reverse=True)


def test_spending_by_category_empty():
    assert spending_by_category([]) == {}


# ---------------------------------------------------------------------------
# spending_by_merchant
# ---------------------------------------------------------------------------

def test_spending_by_merchant_aggregates_same_merchant():
    result = spending_by_merchant(SAMPLE_EXPENSES)
    assert result["Starbucks"] == round(6.75 + 5.25, 2)


def test_spending_by_merchant_sorted_descending():
    result = spending_by_merchant(SAMPLE_EXPENSES)
    amounts = list(result.values())
    assert amounts == sorted(amounts, reverse=True)


# ---------------------------------------------------------------------------
# spending_by_payment_method
# ---------------------------------------------------------------------------

def test_spending_by_payment_method_keys():
    result = spending_by_payment_method(SAMPLE_EXPENSES)
    assert "credit_card" in result
    assert "debit_card" in result
    assert "cash" in result
    assert "mobile_payment" in result


def test_spending_by_payment_method_credit_card_total():
    result = spending_by_payment_method(SAMPLE_EXPENSES)
    assert result["credit_card"] == round(6.75 + 49.99, 2)


# ---------------------------------------------------------------------------
# monthly_summary
# ---------------------------------------------------------------------------

def test_monthly_summary_keys():
    result = monthly_summary(SAMPLE_EXPENSES)
    assert set(result.keys()) == {"2026-01", "2026-02", "2026-03"}


def test_monthly_summary_january_total():
    result = monthly_summary(SAMPLE_EXPENSES)
    assert result["2026-01"] == round(6.75 + 14.20, 2)


def test_monthly_summary_sorted_chronologically():
    result = monthly_summary(SAMPLE_EXPENSES)
    keys = list(result.keys())
    assert keys == sorted(keys)


def test_monthly_summary_empty():
    assert monthly_summary([]) == {}


# ---------------------------------------------------------------------------
# top_merchants
# ---------------------------------------------------------------------------

def test_top_merchants_returns_n_items():
    result = top_merchants(SAMPLE_EXPENSES, n=3)
    assert len(result) == 3


def test_top_merchants_first_is_highest():
    result = top_merchants(SAMPLE_EXPENSES, n=5)
    amounts = [amt for _, amt in result]
    assert amounts == sorted(amounts, reverse=True)


def test_top_merchants_default_n_is_5():
    result = top_merchants(SAMPLE_EXPENSES)
    assert len(result) <= 5


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------

def test_format_report_contains_total():
    report = format_report(SAMPLE_EXPENSES)
    assert "Total Spending" in report


def test_format_report_contains_category_section():
    report = format_report(SAMPLE_EXPENSES)
    assert "By Category" in report
    assert "Food & Dining" in report


def test_format_report_contains_monthly_section():
    report = format_report(SAMPLE_EXPENSES)
    assert "Monthly Summary" in report
    assert "2026-01" in report


def test_format_report_empty_expenses():
    report = format_report([])
    assert "No expenses to report" in report


def test_format_report_custom_title():
    report = format_report(SAMPLE_EXPENSES, title="Q1 Summary")
    assert "Q1 Summary" in report
