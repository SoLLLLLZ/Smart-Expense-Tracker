"""Receipt text parser — converts raw OCR output into structured expense data.

This module is purely string-based and has no I/O or database access,
making it fully unit-testable without Tesseract installed.
"""
import re
from datetime import date, datetime
from typing import Optional

from config import DEFAULT_CATEGORY


# ---------------------------------------------------------------------------
# Top-level parser
# ---------------------------------------------------------------------------

def parse_receipt_text(raw_text: str) -> dict:
    """Parse raw OCR text into a structured dict.

    Returns a dict with keys: date, merchant, amount, category.
    Any field that cannot be extracted will be None.
    The caller (cli.py) prompts the user to fill in missing fields.
    """
    merchant = extract_merchant(raw_text)
    amount = extract_amount(raw_text)
    parsed_date = extract_date(raw_text)
    category = infer_category(merchant, raw_text)

    return {
        "date": parsed_date,
        "merchant": merchant,
        "amount": amount,
        "category": category,
    }


# ---------------------------------------------------------------------------
# Amount extraction
# ---------------------------------------------------------------------------

# Tier 1: strong total keywords (grand total, amount due, balance due)
# Explicitly excludes "subtotal" so it is never mistaken for the final total.
_AMOUNT_STRONG_PATTERN = re.compile(
    r"(?:grand\s*total|total\s*due|amount\s*due|balance\s*due|amt\s*due)"
    r"[:\s*]*"
    r"([\$£€]?\s*\d{1,6}[.,]\d{2})",
    re.IGNORECASE,
)

# Tier 2: plain "total" — but only when NOT preceded by "sub" or "partial"
_AMOUNT_TOTAL_PATTERN = re.compile(
    r"(?<!sub)(?<!partial\s)(?<!sub\s)\btotal\b"
    r"[:\s*]*"
    r"([\$£€]?\s*\d{1,6}[.,]\d{2})",
    re.IGNORECASE,
)

_BARE_AMOUNT_PATTERN = re.compile(
    r"[\$£€]\s*(\d{1,6}[.,]\d{2})",
    re.IGNORECASE,
)


def extract_amount(text: str) -> Optional[float]:
    """Find the total amount from receipt text.

    Strategy:
    1. Look for strong total keywords (grand total, amount due, etc.)
    2. Fall back to plain 'total' (excluding subtotal)
    3. Fall back to the largest bare currency amount in the text.
    Returns None if no amount found.
    """
    # Tier 1: strong keywords
    match = _AMOUNT_STRONG_PATTERN.search(text)
    if match:
        return normalize_amount_string(match.group(1))

    # Tier 2: plain total (not subtotal)
    match = _AMOUNT_TOTAL_PATTERN.search(text)
    if match:
        return normalize_amount_string(match.group(1))

    # Fall back: collect all bare currency amounts and return the largest
    # (the grand total is usually the largest number on a receipt)
    candidates = []
    for m in _BARE_AMOUNT_PATTERN.finditer(text):
        value = normalize_amount_string(m.group(0))
        if value is not None:
            candidates.append(value)

    return max(candidates) if candidates else None


def normalize_amount_string(raw: str) -> Optional[float]:
    """Strip currency symbols, spaces, and commas, then convert to float."""
    if not raw:
        return None
    cleaned = re.sub(r"[\$£€\s]", "", raw)
    # Handle European format: 1.234,56 → 1234.56
    if re.match(r"^\d{1,3}(\.\d{3})*(,\d{2})$", cleaned):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Date extraction
# ---------------------------------------------------------------------------

_DATE_FORMATS = [
    "%m/%d/%Y",   # 03/15/2026
    "%m-%d-%Y",   # 03-15-2026
    "%Y-%m-%d",   # 2026-03-15
    "%d/%m/%Y",   # 15/03/2026
    "%B %d, %Y",  # March 15, 2026
    "%b %d, %Y",  # Mar 15, 2026
    "%B %d %Y",   # March 15 2026
    "%b %d %Y",   # Mar 15 2026
    "%m/%d/%y",   # 03/15/26
    "%d-%b-%Y",   # 15-Mar-2026
]

_DATE_PATTERN = re.compile(
    r"""
    \b(
        \d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}     # 03/15/2026 or 03-15-26
        | \d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}      # 2026-03-15
        | (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|   # Mar 15, 2026
             Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}
        | \d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun| # 15 Mar 2026
                       Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}
        | \d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|   # 15-Mar-2026
                     Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*-\d{4}
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


def extract_date(text: str) -> Optional[date]:
    """Try multiple date format patterns. Returns the first successfully parsed date."""
    for match in _DATE_PATTERN.finditer(text):
        candidate = match.group(1).strip()
        for fmt in _DATE_FORMATS:
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                continue
    return None


# ---------------------------------------------------------------------------
# Merchant extraction
# ---------------------------------------------------------------------------

# Lines that are almost certainly not the merchant name
_SKIP_LINE_PATTERN = re.compile(
    r"""
    ^\s*$                           # blank line
    | ^\s*\d[\d\s\-\/\.]+$         # purely numeric (phone, date, etc.)
    | receipt|invoice|tax\s*id     # document labels
    | thank\s*you|welcome          # pleasantries
    | www\.|http                   # URLs
    | tel:|phone:|fax:             # contact labels
    | \d{5}                        # ZIP codes
    """,
    re.IGNORECASE | re.VERBOSE,
)


def extract_merchant(text: str) -> Optional[str]:
    """Heuristic: the merchant name is typically in the first few non-empty lines."""
    lines = text.splitlines()
    for line in lines[:8]:
        line = line.strip()
        if line and not _SKIP_LINE_PATTERN.search(line):
            # Clean up common OCR artifacts
            cleaned = re.sub(r"[|]{2,}", "", line)  # || artifacts
            cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
            if len(cleaned) >= 2:
                return cleaned
    return None


# ---------------------------------------------------------------------------
# Category inference
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS: dict = {
    "Food & Dining": [
        "starbucks", "mcdonald", "chipotle", "subway", "dunkin", "burger",
        "pizza", "restaurant", "cafe", "coffee", "diner", "sushi", "taco",
        "donut", "bakery", "grill", "bistro", "kitchen", "eatery", "deli",
        "wendy", "chick-fil", "panera", "shake shack", "five guys", "kfc",
        "popeyes", "domino", "papa john", "little caesar", "wingstop",
        "bar ", " bar", "pub", "tavern", "brew",
    ],
    "Transportation": [
        "uber", "lyft", "taxi", "metro", "transit", "parking", "shell",
        "chevron", "exxon", "bp ", " bp", "mobil", "sunoco", "citgo",
        "speedway", "marathon", "fuel", "gas station", "amtrak", "greyhound",
        "delta", "united", "american air", "southwest", "jetblue", "spirit air",
        "toll", "mta",
    ],
    "Shopping": [
        "amazon", "walmart", "target", "costco", "best buy", "home depot",
        "lowe", "ikea", "macy", "nordstrom", "gap", "h&m", "zara", "uniqlo",
        "tj maxx", "marshalls", "ross", "old navy", "banana republic",
        "apple store", "cvs", "walgreens", "rite aid", "dollar",
    ],
    "Entertainment": [
        "netflix", "spotify", "hulu", "disney", "amc", "regal", "cinemark",
        "movie", "cinema", "theater", "theatre", "ticketmaster", "eventbrite",
        "steam", "playstation", "xbox", "nintendo", "twitch", "youtube",
        "concert", "museum", "bowling", "arcade", "escape room",
    ],
    "Healthcare": [
        "pharmacy", "cvs pharmacy", "walgreens pharmacy", "rite aid pharmacy",
        "hospital", "clinic", "urgent care", "doctor", "dental", "optometry",
        "vision", "health", "medical", "prescription", "lab corp", "quest",
    ],
    "Utilities": [
        "at&t", "verizon", "t-mobile", "sprint", "comcast", "xfinity",
        "spectrum", "cox", "electric", "gas company", "water", "internet",
        "utility", "con ed", "pg&e",
    ],
    "Travel": [
        "marriott", "hilton", "hyatt", "airbnb", "expedia", "booking.com",
        "hotels.com", "holiday inn", "best western", "motel", "resort",
        "hertz", "enterprise", "avis", "budget car", "national car",
    ],
}


def infer_category(merchant: Optional[str], text: str) -> str:
    """Keyword-based category inference. Never returns None."""
    search_text = " ".join(filter(None, [merchant, text])).lower()

    for category, keywords in _CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in search_text:
                return category

    return DEFAULT_CATEGORY
