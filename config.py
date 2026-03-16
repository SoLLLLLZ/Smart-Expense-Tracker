import os

DB_PATH: str = os.environ.get("EXPENSE_DB_PATH", "expenses.db")

DATE_FORMAT: str = "%Y-%m-%d"

DEFAULT_CATEGORY: str = "Uncategorized"

SUPPORTED_IMAGE_EXTENSIONS: tuple = (".png", ".jpg", ".jpeg", ".tiff", ".bmp")

VALID_CATEGORIES: list = [
    "Food & Dining",
    "Transportation",
    "Shopping",
    "Entertainment",
    "Healthcare",
    "Utilities",
    "Travel",
    "Uncategorized",
]

VALID_PAYMENT_METHODS: list = [
    "cash",
    "credit_card",
    "debit_card",
    "mobile_payment",
    "other",
]
