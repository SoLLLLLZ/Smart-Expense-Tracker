"""Command-line interface for the Smart Expense Tracker."""
import argparse
import sys
from datetime import date, datetime
from typing import Optional

from config import VALID_CATEGORIES, VALID_PAYMENT_METHODS, DATE_FORMAT
from models import Expense
import crud


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected format: YYYY-MM-DD"
        )


def _parse_amount(value: str) -> float:
    try:
        amount = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid amount '{value}'. Must be a number.")
    if amount <= 0:
        raise argparse.ArgumentTypeError("Amount must be greater than 0.")
    return amount


def _print_table(expenses: list) -> None:
    """Print a list of Expense objects as an aligned text table."""
    if not expenses:
        print("No expenses found.")
        return

    headers = ["ID", "Date", "Merchant", "Amount", "Category", "Payment", "Source"]
    col_widths = [4, 10, 20, 8, 16, 14, 6]

    # Adjust merchant column width to fit data
    if expenses:
        max_merchant = max(len(e.merchant) for e in expenses)
        col_widths[2] = max(col_widths[2], max_merchant)

    def fmt_row(row, is_header=False):
        if is_header:
            amount_col = str(row[3]).ljust(9)
        else:
            amount_col = ("$" + f"{row[3]:.2f}").rjust(9)
        return (
            f"{str(row[0]).ljust(col_widths[0])}  "
            f"{str(row[1]).ljust(col_widths[1])}  "
            f"{str(row[2]).ljust(col_widths[2])}  "
            f"{amount_col}  "
            f"{str(row[4]).ljust(col_widths[4])}  "
            f"{str(row[5]).ljust(col_widths[5])}  "
            f"{str(row[6]).ljust(col_widths[6])}"
        )

    separator = "-" * (sum(col_widths) + len(col_widths) * 2 + 10)
    print(fmt_row(headers, is_header=True))
    print(separator)
    for e in expenses:
        print(fmt_row([
            e.id,
            e.date.strftime(DATE_FORMAT),
            e.merchant,
            e.amount,
            e.category,
            e.payment_method,
            e.source,
        ]))
    print(separator)
    print(f"  {len(expenses)} record(s)")


def _prompt(label: str, default: Optional[str] = None, validator=None) -> str:
    """Interactive prompt. Re-prompts on validation failure."""
    prompt_str = f"{label}"
    if default is not None:
        prompt_str += f" [{default}]"
    prompt_str += ": "

    while True:
        value = input(prompt_str).strip()
        if not value and default is not None:
            value = default
        if not value:
            print(f"  {label} cannot be empty.")
            continue
        if validator:
            error = validator(value)
            if error:
                print(f"  {error}")
                continue
        return value


def _choose(label: str, options: list, default: Optional[str] = None) -> str:
    """Numbered menu prompt."""
    print(f"\n{label}:")
    for i, opt in enumerate(options, 1):
        marker = " (default)" if opt == default else ""
        print(f"  {i}. {opt}{marker}")
    while True:
        raw = input("Enter number or value: ").strip()
        if not raw and default:
            return default
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]
        if raw in options:
            return raw
        print(f"  Invalid choice. Enter a number 1-{len(options)} or the value directly.")


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_add(args: argparse.Namespace) -> None:
    """Add a new expense interactively or via flags."""
    print("\n-- Add Expense --")

    # Date
    if args.date:
        expense_date = args.date
    else:
        raw = _prompt("Date (YYYY-MM-DD)", default=date.today().strftime(DATE_FORMAT))
        expense_date = _parse_date(raw)

    # Merchant
    merchant = args.merchant or _prompt("Merchant")

    # Amount
    if args.amount:
        amount = args.amount
    else:
        amount = float(_prompt("Amount", validator=lambda v: (
            None if v.replace(".", "", 1).isdigit() and float(v) > 0
            else "Must be a positive number."
        )))

    # Category
    category = args.category or _choose("Category", VALID_CATEGORIES, default="Uncategorized")

    # Payment method
    payment_method = args.payment_method or _choose(
        "Payment method", VALID_PAYMENT_METHODS, default="other"
    )

    expense = Expense(
        date=expense_date,
        merchant=merchant,
        amount=amount,
        category=category,
        payment_method=payment_method,
        source="manual",
    )

    row_id = crud.insert_expense(expense)
    print(f"\nExpense added with ID {row_id}.")


def cmd_view(args: argparse.Namespace) -> None:
    """Display all expenses."""
    order_by = args.order_by or "date"
    expenses = crud.get_all_expenses(order_by=order_by, descending=not args.asc)
    if args.limit:
        expenses = expenses[: args.limit]
    print(f"\n-- All Expenses (ordered by {order_by}) --")
    _print_table(expenses)


def cmd_search(args: argparse.Namespace) -> None:
    """Search expenses with filters."""
    results = crud.search_expenses(
        category=args.category,
        merchant=args.merchant,
        date_from=args.date_from,
        date_to=args.date_to,
        payment_method=args.payment_method,
        min_amount=args.min_amount,
        max_amount=args.max_amount,
    )
    print(f"\n-- Search Results --")
    _print_table(results)


def cmd_update(args: argparse.Namespace) -> None:
    """Update an existing expense."""
    expense = crud.get_expense_by_id(args.id)
    if expense is None:
        print(f"Expense ID {args.id} not found.")
        sys.exit(1)

    print(f"\n-- Update Expense ID {args.id} --")
    print("Press Enter to keep the current value.\n")

    new_date = args.date
    if new_date is None and not args.non_interactive:
        raw = input(f"Date [{expense.date.strftime(DATE_FORMAT)}]: ").strip()
        if raw:
            new_date = _parse_date(raw)

    new_merchant = args.merchant
    if new_merchant is None and not args.non_interactive:
        raw = input(f"Merchant [{expense.merchant}]: ").strip()
        if raw:
            new_merchant = raw

    new_amount = args.amount
    if new_amount is None and not args.non_interactive:
        raw = input(f"Amount [{expense.amount}]: ").strip()
        if raw:
            new_amount = _parse_amount(raw)

    new_category = args.category
    if new_category is None and not args.non_interactive:
        raw = input(f"Category [{expense.category}]: ").strip()
        if raw:
            if raw not in VALID_CATEGORIES:
                print(f"Invalid category. Valid: {', '.join(VALID_CATEGORIES)}")
                sys.exit(1)
            new_category = raw

    new_payment = args.payment_method
    if new_payment is None and not args.non_interactive:
        raw = input(f"Payment method [{expense.payment_method}]: ").strip()
        if raw:
            if raw not in VALID_PAYMENT_METHODS:
                print(f"Invalid payment method. Valid: {', '.join(VALID_PAYMENT_METHODS)}")
                sys.exit(1)
            new_payment = raw

    updated = crud.update_expense(
        args.id,
        date=new_date,
        merchant=new_merchant,
        amount=new_amount,
        category=new_category,
        payment_method=new_payment,
    )

    if updated:
        print(f"\nExpense ID {args.id} updated.")
    else:
        print("No changes made.")


def cmd_delete(args: argparse.Namespace) -> None:
    """Delete an expense after confirmation."""
    expense = crud.get_expense_by_id(args.id)
    if expense is None:
        print(f"Expense ID {args.id} not found.")
        sys.exit(1)

    print(f"\n-- Delete Expense ID {args.id} --")
    print(f"  {expense.date}  {expense.merchant}  ${expense.amount:.2f}  {expense.category}")

    if not args.yes:
        confirm = input("\nAre you sure? (y/N): ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Cancelled.")
            return

    crud.delete_expense(args.id)
    print(f"Expense ID {args.id} deleted.")


def cmd_upload_receipt(args: argparse.Namespace) -> None:
    """OCR a receipt image and insert the parsed expense."""
    # Import here so the rest of the CLI works without pytesseract installed
    try:
        from ocr import extract_text_from_image, is_tesseract_available
        from parser import parse_receipt_text
    except ImportError as exc:
        print(f"Missing dependency: {exc}")
        print("Run: pip install pytesseract Pillow")
        sys.exit(1)

    if not is_tesseract_available():
        print("Tesseract not found. Install it with:")
        print("  macOS:  brew install tesseract")
        print("  Linux:  sudo apt install tesseract-ocr")
        sys.exit(1)

    print(f"\nProcessing receipt: {args.image_path}")
    raw_text = extract_text_from_image(args.image_path)

    if not raw_text.strip():
        print("Could not extract any text from the image. Check image quality.")
        sys.exit(1)

    parsed = parse_receipt_text(raw_text)
    print("\n-- Parsed Receipt Data --")
    for key, val in parsed.items():
        print(f"  {key}: {val if val is not None else '(not found)'}")

    print("\nFill in any missing fields (press Enter to accept parsed value):\n")

    # Date
    default_date = parsed["date"].strftime(DATE_FORMAT) if parsed["date"] else date.today().strftime(DATE_FORMAT)
    raw = input(f"Date [{default_date}]: ").strip()
    expense_date = _parse_date(raw) if raw else (parsed["date"] or date.today())

    # Merchant
    default_merchant = parsed["merchant"] or ""
    merchant = _prompt("Merchant", default=default_merchant or None)

    # Amount
    default_amount = str(parsed["amount"]) if parsed["amount"] else ""
    while True:
        raw = input(f"Amount [{default_amount}]: ").strip()
        if not raw and parsed["amount"]:
            amount = parsed["amount"]
            break
        try:
            amount = float(raw)
            if amount > 0:
                break
            print("  Must be a positive number.")
        except ValueError:
            print("  Must be a number.")

    # Category
    default_cat = parsed.get("category", "Uncategorized")
    category = _choose("Category", VALID_CATEGORIES, default=default_cat)

    # Payment method
    payment_method = _choose("Payment method", VALID_PAYMENT_METHODS, default="other")

    expense = Expense(
        date=expense_date,
        merchant=merchant,
        amount=amount,
        category=category,
        payment_method=payment_method,
        source="ocr",
    )

    confirm = input("\nInsert this expense? (Y/n): ").strip().lower()
    if confirm in ("", "y", "yes"):
        row_id = crud.insert_expense(expense)
        print(f"Expense added with ID {row_id}.")
    else:
        print("Cancelled.")


def cmd_report(args: argparse.Namespace) -> None:
    """Generate a spending analytics report."""
    import analytics

    expenses = crud.search_expenses(
        category=args.category,
        date_from=args.date_from,
        date_to=args.date_to,
    )
    title = "Expense Report"
    if args.date_from or args.date_to:
        parts = []
        if args.date_from:
            parts.append(f"from {args.date_from}")
        if args.date_to:
            parts.append(f"to {args.date_to}")
        title += " (" + " ".join(parts) + ")"
    print(analytics.format_report(expenses, title=title))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="expense_tracker",
        description="Smart Expense Tracker — manage and analyze your expenses.",
    )
    parser.add_argument("--gui", action="store_true", help="Launch the graphical interface.")
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # add
    p_add = subparsers.add_parser("add", help="Add a new expense.")
    p_add.add_argument("--date", type=_parse_date, metavar="YYYY-MM-DD")
    p_add.add_argument("--merchant", type=str)
    p_add.add_argument("--amount", type=_parse_amount)
    p_add.add_argument("--category", type=str, choices=VALID_CATEGORIES)
    p_add.add_argument("--payment-method", dest="payment_method",
                       type=str, choices=VALID_PAYMENT_METHODS)
    p_add.set_defaults(func=cmd_add)

    # view
    p_view = subparsers.add_parser("view", help="View all expenses.")
    p_view.add_argument("--order-by", dest="order_by",
                        choices=["date", "amount", "merchant", "category", "created_at"],
                        default="date")
    p_view.add_argument("--asc", action="store_true", help="Sort ascending (default: descending).")
    p_view.add_argument("--limit", type=int, metavar="N")
    p_view.set_defaults(func=cmd_view)

    # search
    p_search = subparsers.add_parser("search", help="Search expenses with filters.")
    p_search.add_argument("--category", type=str)
    p_search.add_argument("--merchant", type=str)
    p_search.add_argument("--from", dest="date_from", type=_parse_date, metavar="YYYY-MM-DD")
    p_search.add_argument("--to", dest="date_to", type=_parse_date, metavar="YYYY-MM-DD")
    p_search.add_argument("--payment-method", dest="payment_method", type=str)
    p_search.add_argument("--min-amount", dest="min_amount", type=float)
    p_search.add_argument("--max-amount", dest="max_amount", type=float)
    p_search.set_defaults(func=cmd_search)

    # update
    p_update = subparsers.add_parser("update", help="Update an existing expense.")
    p_update.add_argument("--id", type=int, required=True, metavar="ID")
    p_update.add_argument("--date", type=_parse_date, metavar="YYYY-MM-DD")
    p_update.add_argument("--merchant", type=str)
    p_update.add_argument("--amount", type=_parse_amount)
    p_update.add_argument("--category", type=str, choices=VALID_CATEGORIES)
    p_update.add_argument("--payment-method", dest="payment_method",
                          type=str, choices=VALID_PAYMENT_METHODS)
    p_update.add_argument("--non-interactive", dest="non_interactive",
                          action="store_true", help="Skip prompts, only use provided flags.")
    p_update.set_defaults(func=cmd_update)

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete an expense.")
    p_delete.add_argument("--id", type=int, required=True, metavar="ID")
    p_delete.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt.")
    p_delete.set_defaults(func=cmd_delete)

    # upload-receipt
    p_receipt = subparsers.add_parser("upload-receipt", help="Add an expense from a receipt image.")
    p_receipt.add_argument("image_path", metavar="IMAGE_PATH")
    p_receipt.set_defaults(func=cmd_upload_receipt)

    # report
    p_report = subparsers.add_parser("report", help="Show a spending analytics report.")
    p_report.add_argument("--from", dest="date_from", type=_parse_date, metavar="YYYY-MM-DD")
    p_report.add_argument("--to", dest="date_to", type=_parse_date, metavar="YYYY-MM-DD")
    p_report.add_argument("--category", type=str)
    p_report.set_defaults(func=cmd_report)

    return parser
