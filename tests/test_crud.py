"""Tests for crud.py using an in-memory SQLite database."""
import sys
import os

# Allow imports from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import date

from database import _execute_schema, get_connection
from models import Expense
from crud import (
    insert_expense,
    get_expense_by_id,
    get_all_expenses,
    search_expenses,
    update_expense,
    delete_expense,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path):
    """Return a path to a fresh temporary SQLite database for each test."""
    db_path = str(tmp_path / "test.db")
    conn = get_connection(db_path)
    _execute_schema(conn)
    conn.commit()
    conn.close()
    return db_path


def make_expense(**kwargs) -> Expense:
    defaults = dict(
        date=date(2026, 3, 15),
        merchant="Starbucks",
        amount=6.75,
        category="Food & Dining",
        payment_method="credit_card",
        source="manual",
    )
    defaults.update(kwargs)
    return Expense(**defaults)


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def test_insert_expense_returns_id(db):
    expense = make_expense()
    row_id = insert_expense(expense, db_path=db)
    assert isinstance(row_id, int)
    assert row_id == 1


def test_insert_multiple_expenses_increments_id(db):
    id1 = insert_expense(make_expense(merchant="Starbucks"), db_path=db)
    id2 = insert_expense(make_expense(merchant="Chipotle"), db_path=db)
    assert id2 == id1 + 1


def test_insert_invalid_expense_raises_value_error(db):
    bad = make_expense(amount=-5.0)
    with pytest.raises(ValueError, match="Amount must be a positive number"):
        insert_expense(bad, db_path=db)


def test_insert_invalid_category_raises_value_error(db):
    bad = make_expense(category="NotACategory")
    with pytest.raises(ValueError):
        insert_expense(bad, db_path=db)


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def test_get_expense_by_id_returns_correct_expense(db):
    expense = make_expense(merchant="Uber", amount=14.20)
    row_id = insert_expense(expense, db_path=db)

    fetched = get_expense_by_id(row_id, db_path=db)
    assert fetched is not None
    assert fetched.merchant == "Uber"
    assert fetched.amount == 14.20
    assert fetched.id == row_id


def test_get_expense_by_id_returns_none_for_missing(db):
    result = get_expense_by_id(999, db_path=db)
    assert result is None


def test_get_all_expenses_returns_all(db):
    insert_expense(make_expense(merchant="A"), db_path=db)
    insert_expense(make_expense(merchant="B"), db_path=db)
    insert_expense(make_expense(merchant="C"), db_path=db)

    results = get_all_expenses(db_path=db)
    assert len(results) == 3


def test_get_all_expenses_empty_db(db):
    results = get_all_expenses(db_path=db)
    assert results == []


def test_get_all_expenses_invalid_order_by_raises(db):
    with pytest.raises(ValueError):
        get_all_expenses(db_path=db, order_by="nonexistent_column")


# ---------------------------------------------------------------------------
# SEARCH (filtered read — satisfies assignment requirement)
# ---------------------------------------------------------------------------

def test_search_by_category(db):
    insert_expense(make_expense(merchant="Starbucks", category="Food & Dining"), db_path=db)
    insert_expense(make_expense(merchant="Uber", category="Transportation"), db_path=db)

    results = search_expenses(db_path=db, category="Food & Dining")
    assert len(results) == 1
    assert results[0].merchant == "Starbucks"


def test_search_by_merchant_partial_match(db):
    insert_expense(make_expense(merchant="Starbucks Reserve"), db_path=db)
    insert_expense(make_expense(merchant="Chipotle"), db_path=db)

    results = search_expenses(db_path=db, merchant="Starbucks")
    assert len(results) == 1
    assert "Starbucks" in results[0].merchant


def test_search_by_amount_range(db):
    insert_expense(make_expense(merchant="A", amount=5.00), db_path=db)
    insert_expense(make_expense(merchant="B", amount=15.00), db_path=db)
    insert_expense(make_expense(merchant="C", amount=50.00), db_path=db)

    results = search_expenses(db_path=db, min_amount=10.0, max_amount=20.0)
    assert len(results) == 1
    assert results[0].merchant == "B"


def test_search_by_date_range(db):
    insert_expense(make_expense(merchant="Early", date=date(2026, 1, 1)), db_path=db)
    insert_expense(make_expense(merchant="Late", date=date(2026, 12, 31)), db_path=db)

    results = search_expenses(
        db_path=db,
        date_from=date(2026, 6, 1),
        date_to=date(2026, 12, 31),
    )
    assert len(results) == 1
    assert results[0].merchant == "Late"


def test_search_no_results_returns_empty_list(db):
    insert_expense(make_expense(), db_path=db)
    results = search_expenses(db_path=db, category="Travel")
    assert results == []


def test_search_combined_filters(db):
    insert_expense(make_expense(merchant="Starbucks", category="Food & Dining", amount=6.75), db_path=db)
    insert_expense(make_expense(merchant="Uber", category="Transportation", amount=14.20), db_path=db)

    results = search_expenses(db_path=db, category="Food & Dining", max_amount=10.0)
    assert len(results) == 1
    assert results[0].merchant == "Starbucks"


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def test_update_expense_merchant(db):
    row_id = insert_expense(make_expense(merchant="Old Name"), db_path=db)
    updated = update_expense(row_id, db_path=db, merchant="New Name")
    assert updated is True

    fetched = get_expense_by_id(row_id, db_path=db)
    assert fetched.merchant == "New Name"


def test_update_expense_amount(db):
    row_id = insert_expense(make_expense(amount=10.00), db_path=db)
    update_expense(row_id, db_path=db, amount=20.00)

    fetched = get_expense_by_id(row_id, db_path=db)
    assert fetched.amount == 20.00


def test_update_expense_invalid_amount_raises(db):
    row_id = insert_expense(make_expense(), db_path=db)
    with pytest.raises(ValueError, match="Amount must be a positive number"):
        update_expense(row_id, db_path=db, amount=-1.0)


def test_update_nonexistent_expense_returns_false(db):
    result = update_expense(999, db_path=db, merchant="Ghost")
    assert result is False


def test_update_no_fields_returns_false(db):
    row_id = insert_expense(make_expense(), db_path=db)
    result = update_expense(row_id, db_path=db)
    assert result is False


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def test_delete_expense_removes_record(db):
    row_id = insert_expense(make_expense(), db_path=db)
    deleted = delete_expense(row_id, db_path=db)
    assert deleted is True
    assert get_expense_by_id(row_id, db_path=db) is None


def test_delete_nonexistent_expense_returns_false(db):
    result = delete_expense(999, db_path=db)
    assert result is False


def test_delete_only_removes_target_record(db):
    id1 = insert_expense(make_expense(merchant="Keep"), db_path=db)
    id2 = insert_expense(make_expense(merchant="Delete Me"), db_path=db)

    delete_expense(id2, db_path=db)

    assert get_expense_by_id(id1, db_path=db) is not None
    assert get_expense_by_id(id2, db_path=db) is None
