"""Tests for parser.py — pure string operations, no Tesseract required."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from parser import (
    extract_amount,
    extract_date,
    extract_merchant,
    infer_category,
    normalize_amount_string,
    parse_receipt_text,
)


# ---------------------------------------------------------------------------
# normalize_amount_string
# ---------------------------------------------------------------------------

def test_normalize_dollar_sign():
    assert normalize_amount_string("$6.75") == 6.75

def test_normalize_with_space():
    assert normalize_amount_string("$ 14.20") == 14.20

def test_normalize_with_comma():
    assert normalize_amount_string("$1,234.56") == 1234.56

def test_normalize_no_symbol():
    assert normalize_amount_string("49.99") == 49.99

def test_normalize_invalid_returns_none():
    assert normalize_amount_string("abc") is None

def test_normalize_empty_returns_none():
    assert normalize_amount_string("") is None


# ---------------------------------------------------------------------------
# extract_amount
# ---------------------------------------------------------------------------

RECEIPT_WITH_TOTAL = """
STARBUCKS
123 Main St

Latte         $5.25
Muffin        $3.50

TOTAL         $8.75
"""

RECEIPT_AMOUNT_DUE = """
Quick Mart

Item 1        $2.00
Item 2        $4.00

AMOUNT DUE:   $6.00
"""

RECEIPT_NO_LABEL = """
Some Store

$3.99
$12.50
$1.00
"""

RECEIPT_GRAND_TOTAL = """
Restaurant Name

Burger        $9.99
Fries         $3.99
Drink         $2.49

Subtotal      $16.47
Tax           $1.32
Grand Total   $17.79
"""

def test_extract_amount_with_total_label():
    assert extract_amount(RECEIPT_WITH_TOTAL) == 8.75

def test_extract_amount_with_amount_due():
    assert extract_amount(RECEIPT_AMOUNT_DUE) == 6.00

def test_extract_amount_grand_total():
    assert extract_amount(RECEIPT_GRAND_TOTAL) == 17.79

def test_extract_amount_no_label_returns_largest():
    # No label — falls back to largest bare currency amount
    result = extract_amount(RECEIPT_NO_LABEL)
    assert result == 12.50

def test_extract_amount_empty_text_returns_none():
    assert extract_amount("") is None

def test_extract_amount_no_amounts_returns_none():
    assert extract_amount("Thank you for shopping!") is None


# ---------------------------------------------------------------------------
# extract_date
# ---------------------------------------------------------------------------

def test_extract_date_slash_format():
    assert extract_date("Date: 03/15/2026") == date(2026, 3, 15)

def test_extract_date_iso_format():
    assert extract_date("2026-03-15") == date(2026, 3, 15)

def test_extract_date_long_month():
    assert extract_date("March 15, 2026") == date(2026, 3, 15)

def test_extract_date_short_month():
    assert extract_date("Mar 15, 2026") == date(2026, 3, 15)

def test_extract_date_short_month_no_comma():
    assert extract_date("Mar 15 2026") == date(2026, 3, 15)

def test_extract_date_dash_format():
    assert extract_date("03-15-2026") == date(2026, 3, 15)

def test_extract_date_in_full_receipt():
    text = "STARBUCKS\n123 Main St\n03/15/2026\nTotal $6.75"
    result = extract_date(text)
    assert result == date(2026, 3, 15)

def test_extract_date_no_date_returns_none():
    assert extract_date("No date here at all.") is None

def test_extract_date_empty_returns_none():
    assert extract_date("") is None


# ---------------------------------------------------------------------------
# extract_merchant
# ---------------------------------------------------------------------------

def test_extract_merchant_first_line():
    text = "STARBUCKS\n123 Main St\nTotal $6.75"
    assert extract_merchant(text) == "STARBUCKS"

def test_extract_merchant_skips_blank_lines():
    text = "\n\nChipotle\n123 Broadway\nTotal $12.50"
    assert extract_merchant(text) == "Chipotle"

def test_extract_merchant_skips_numeric_lines():
    text = "12345\nUber Eats\nDelivery $3.00\nTotal $15.00"
    assert extract_merchant(text) == "Uber Eats"

def test_extract_merchant_skips_url():
    text = "www.receipt.com\nAmazon\nOrder total $49.99"
    assert extract_merchant(text) == "Amazon"

def test_extract_merchant_empty_text_returns_none():
    assert extract_merchant("") is None

def test_extract_merchant_all_blank_returns_none():
    assert extract_merchant("\n\n\n") is None


# ---------------------------------------------------------------------------
# infer_category
# ---------------------------------------------------------------------------

def test_infer_category_starbucks():
    assert infer_category("Starbucks", "") == "Food & Dining"

def test_infer_category_uber():
    assert infer_category("Uber", "") == "Transportation"

def test_infer_category_amazon():
    assert infer_category("Amazon", "") == "Shopping"

def test_infer_category_netflix():
    assert infer_category("Netflix", "") == "Entertainment"

def test_infer_category_from_text_fallback():
    # Merchant name unknown, but body text has a keyword
    assert infer_category(None, "parking garage downtown") == "Transportation"

def test_infer_category_unknown_returns_default():
    assert infer_category("XYZ Random Store", "no keywords here") == "Uncategorized"

def test_infer_category_none_merchant():
    # Should not crash when merchant is None
    result = infer_category(None, "")
    assert result == "Uncategorized"


# ---------------------------------------------------------------------------
# parse_receipt_text (integration)
# ---------------------------------------------------------------------------

FULL_RECEIPT = """
STARBUCKS RESERVE
789 Coffee Lane
New York, NY 10001

03/15/2026

Latte              $5.25
Blueberry Muffin   $3.50

Subtotal           $8.75
Tax                $0.79
TOTAL              $9.54

Thank you!
"""

def test_parse_receipt_text_extracts_all_fields():
    result = parse_receipt_text(FULL_RECEIPT)
    assert result["merchant"] is not None
    assert "STARBUCKS" in result["merchant"].upper()
    assert result["amount"] == 9.54
    assert result["date"] == date(2026, 3, 15)
    assert result["category"] == "Food & Dining"

def test_parse_receipt_text_empty_returns_none_fields():
    result = parse_receipt_text("")
    assert result["merchant"] is None
    assert result["amount"] is None
    assert result["date"] is None
    assert result["category"] == "Uncategorized"

def test_parse_receipt_text_returns_dict_with_expected_keys():
    result = parse_receipt_text("anything")
    assert set(result.keys()) == {"date", "merchant", "amount", "category"}
