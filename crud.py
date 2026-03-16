import sqlite3
from datetime import date
from typing import Optional

from database import get_connection, _execute_schema
from models import Expense
from config import DATE_FORMAT


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def insert_expense(expense: Expense, db_path: Optional[str] = None) -> int:
    """Insert a new expense record. Returns the new row's id.

    Raises ValueError if expense.validate() returns errors.
    Raises sqlite3.IntegrityError on constraint violations.
    """
    errors = expense.validate()
    if errors:
        raise ValueError("Invalid expense:\n" + "\n".join(f"  - {e}" for e in errors))

    sql = """
        INSERT INTO expenses (date, merchant, amount, category, payment_method, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    params = (
        expense.date.strftime(DATE_FORMAT),
        expense.merchant.strip(),
        expense.amount,
        expense.category,
        expense.payment_method,
        expense.source,
    )

    conn = get_connection(db_path)
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def get_expense_by_id(expense_id: int, db_path: Optional[str] = None) -> Optional[Expense]:
    """Return a single Expense or None if not found."""
    sql = """
        SELECT id, date, merchant, amount, category, payment_method, source, created_at
        FROM expenses
        WHERE id = ?
    """
    conn = get_connection(db_path)
    try:
        row = conn.execute(sql, (expense_id,)).fetchone()
        return Expense.from_row(tuple(row)) if row else None
    finally:
        conn.close()


_ALLOWED_ORDER_COLUMNS = {"date", "amount", "merchant", "category", "created_at"}


def get_all_expenses(
    db_path: Optional[str] = None,
    order_by: str = "date",
    descending: bool = True,
) -> list:
    """Return all expenses ordered by the specified column.

    Raises ValueError for invalid order_by values (prevents SQL injection).
    """
    if order_by not in _ALLOWED_ORDER_COLUMNS:
        raise ValueError(
            f"Invalid order_by '{order_by}'. "
            f"Allowed: {', '.join(sorted(_ALLOWED_ORDER_COLUMNS))}"
        )
    direction = "DESC" if descending else "ASC"
    sql = f"""
        SELECT id, date, merchant, amount, category, payment_method, source, created_at
        FROM expenses
        ORDER BY {order_by} {direction}
    """
    conn = get_connection(db_path)
    try:
        rows = conn.execute(sql).fetchall()
        return [Expense.from_row(tuple(r)) for r in rows]
    finally:
        conn.close()


def search_expenses(
    db_path: Optional[str] = None,
    category: Optional[str] = None,
    merchant: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    payment_method: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    source: Optional[str] = None,
    order_by: str = "date",
    descending: bool = True,
) -> list:
    """Filtered and sorted query. All filters are optional and ANDed together.

    Uses parameterized queries exclusively — no string interpolation on user data.
    Returns an empty list if no results match.
    """
    if order_by not in _ALLOWED_ORDER_COLUMNS:
        raise ValueError(
            f"Invalid order_by '{order_by}'. "
            f"Allowed: {', '.join(sorted(_ALLOWED_ORDER_COLUMNS))}"
        )

    conditions = []
    params = []

    if category is not None:
        conditions.append("category = ?")
        params.append(category)
    if merchant is not None:
        conditions.append("merchant LIKE ?")
        params.append(f"%{merchant}%")
    if date_from is not None:
        conditions.append("date >= ?")
        params.append(date_from.strftime(DATE_FORMAT))
    if date_to is not None:
        conditions.append("date <= ?")
        params.append(date_to.strftime(DATE_FORMAT))
    if payment_method is not None:
        conditions.append("payment_method = ?")
        params.append(payment_method)
    if min_amount is not None:
        conditions.append("amount >= ?")
        params.append(min_amount)
    if max_amount is not None:
        conditions.append("amount <= ?")
        params.append(max_amount)
    if source is not None:
        conditions.append("source = ?")
        params.append(source)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    direction = "DESC" if descending else "ASC"
    sql = f"""
        SELECT id, date, merchant, amount, category, payment_method, source, created_at
        FROM expenses
        {where_clause}
        ORDER BY {order_by} {direction}
    """

    conn = get_connection(db_path)
    try:
        rows = conn.execute(sql, params).fetchall()
        return [Expense.from_row(tuple(r)) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def update_expense(
    expense_id: int,
    db_path: Optional[str] = None,
    date: Optional[date] = None,
    merchant: Optional[str] = None,
    amount: Optional[float] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
) -> bool:
    """Partial update: only columns passed as non-None are modified.

    Returns True if a row was updated, False if expense_id was not found.
    Note: 'source' and 'created_at' are intentionally not updatable.
    """
    updates = []
    params = []

    if date is not None:
        updates.append("date = ?")
        params.append(date.strftime(DATE_FORMAT))
    if merchant is not None:
        updates.append("merchant = ?")
        params.append(merchant.strip())
    if amount is not None:
        if amount <= 0:
            raise ValueError("Amount must be a positive number.")
        updates.append("amount = ?")
        params.append(amount)
    if category is not None:
        updates.append("category = ?")
        params.append(category)
    if payment_method is not None:
        updates.append("payment_method = ?")
        params.append(payment_method)

    if not updates:
        return False  # nothing to update

    params.append(expense_id)
    sql = f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?"

    conn = get_connection(db_path)
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def delete_expense(expense_id: int, db_path: Optional[str] = None) -> bool:
    """Delete an expense by id.

    Returns True if a row was deleted, False if not found.
    """
    sql = "DELETE FROM expenses WHERE id = ?"
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(sql, (expense_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
