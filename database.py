import sqlite3
from typing import Optional

from config import DB_PATH


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Open and return a sqlite3 connection with row_factory set to sqlite3.Row.

    Uses config.DB_PATH if db_path is not provided.
    Caller is responsible for closing the connection or using it as a context manager.
    """
    path = db_path if db_path is not None else DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(db_path: Optional[str] = None) -> None:
    """Create the expenses table and indexes if they do not exist.

    Safe to call on every application startup — uses IF NOT EXISTS.
    """
    conn = get_connection(db_path)
    try:
        _execute_schema(conn)
        conn.commit()
    finally:
        conn.close()


def _execute_schema(conn: sqlite3.Connection) -> None:
    """Execute the CREATE TABLE and CREATE INDEX statements."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS expenses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT    NOT NULL,
            merchant        TEXT    NOT NULL,
            amount          REAL    NOT NULL CHECK (amount > 0),
            category        TEXT    NOT NULL DEFAULT 'Uncategorized',
            payment_method  TEXT    NOT NULL DEFAULT 'other',
            source          TEXT    NOT NULL DEFAULT 'manual',
            created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_expenses_date
            ON expenses (date);

        CREATE INDEX IF NOT EXISTS idx_expenses_category
            ON expenses (category);
    """)
