# Smart Expense Tracker

The app I built is a Smart Expense Tracker. This is a local desktop application that tracks personal expenses and records the merchant, amount, date, category, and payment method for each transaction. I've found that I often have trouble managing my expenses when they are all seperated and managed through different mediums (credit card, debit card, zelle, US card, and Canadian card). So I wanted an organized space where I could track all my expenses. Additionally, I've also found that I usually throw out receipts without a second thought. Therefore, I decided to make receipts more useful by giving my app the option to upload the receipt and it will automatically log the expense. This is an application built with Python and SQLite. Supports manual entry, receipt OCR, spending analytics, and an interactive GUI.

## Features

- Add, view, update, and delete expenses (full CRUD)
- Filter and sort expenses by category, merchant, date range, amount, and payment method
- Upload receipt images — OCR extracts merchant, amount, and date automatically
- Spending analytics: totals by category, payment method, monthly summaries, top merchants
- Optional tkinter desktop GUI

## Database Schema

```sql
CREATE TABLE expenses (
    id              INTEGER/Text     Constraints,
    date            TEXT             NOT NULL,
    merchant        TEXT             NOT NULL,
    amount          INTEGER          NOT NULL CHECK (amount > 0),
    category        TEXT             NOT NULL DEFAULT 'Uncategorized',
    payment_method  TEXT             NOT NULL DEFAULT 'other',
    source          TEXT             NOT NULL DEFAULT 'manual',
    created_at      TEXT             NOT NULL DEFAULT (datetime('now', 'localtime'))
);
```

## CRUD Operations

Create — Add a new expense. You can do this in the terminal or in the interactive GUI:

python main.py add --merchant "Starbucks" --amount 6.75 --category "Food & Dining" --payment-method credit_card --date 2026-03-15
# or interactively: python main.py add
In the GUI: click + Add, fill in the dialog, click Save.

Read — View and search expenses. You can do this in the terminal or in the interactive GUI:

python main.py view     # all expenses
python main.py search --category "Food & Dining"
python main.py search --from 2026-01-01 --to 2026-03-31
In the GUI: the table loads on startup; use the search bar, time filters (Day/Week), or click column headers to sort.

Update — Edit an existing expense by ID. You can do this in the terminal or in the interactive GUI:

python main.py update --id 1 --amount 7.50
In the GUI: double-click any row (or select it and click ✏ Edit), change fields, click Save.

Delete — Remove an expense by ID. You can do this in the terminal or in the interactive GUI:

python main.py delete --id 1
In the GUI: select a row and click 🗑 Delete — a confirmation prompt appears before deletion.


## Requirements

**Python:** 3.10+

**Python packages:**
```
pip install -r requirements.txt
```

**Tesseract binary** (only needed for receipt OCR):
```bash
# macOS
brew install tesseract

# Ubuntu / Debian
sudo apt install tesseract-ocr
```

## Setup

```bash
git clone https://github.com/SoLLLLLZ/Smart-Expense-Tracker.git
cd Smart-Expense-Tracker
pip install -r requirements.txt
```

The SQLite database (`expenses.db`) is created automatically on first run.

## Usage

### CLI

```bash
# Show all commands
python main.py

# Add an expense (interactive)
python main.py add

# Add an expense via flags
python main.py add --merchant "Starbucks" --amount 6.75 --category "Food & Dining" --payment-method credit_card --date 2026-03-15

# View all expenses
python main.py view

# View sorted by amount
python main.py view --order-by amount

# Search with filters
python main.py search --category "Food & Dining"
python main.py search --merchant "Uber" --min-amount 10
python main.py search --from 2026-01-01 --to 2026-03-31

# Update an expense
python main.py update --id 1 --amount 7.50

# Delete an expense
python main.py delete --id 1

# Upload a receipt image (requires Tesseract)
python main.py upload-receipt receipt.jpg

# Analytics report
python main.py report
python main.py report --from 2026-01-01 --to 2026-03-31
python main.py report --category "Food & Dining"
```

### GUI

```bash
python main.py --gui
```

- Double-click any row to edit it
- Click column headers to sort
- Use the search bar to filter by merchant name in real time

## Project Structure

```
├── main.py          # Entry point
├── config.py        # Constants (DB path, valid categories, etc.)
├── models.py        # Expense dataclass
├── database.py      # SQLite connection and schema
├── crud.py          # Create, Read, Update, Delete operations
├── analytics.py     # Spending analytics (pure functions)
├── cli.py           # Command-line interface
├── ocr.py           # Receipt image OCR
├── parser.py        # Receipt text parsing
├── gui.py           # Optional tkinter GUI
├── requirements.txt
└── tests/
    ├── test_crud.py
    ├── test_analytics.py
    └── test_parser.py
```

## Running Tests

```bash
python -m pytest tests/ -v
```

Tests for `crud.py` and `analytics.py` use an in-memory SQLite database. Tests for `parser.py` use hardcoded strings — no Tesseract installation required.
