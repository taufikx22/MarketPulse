from datetime import date
from app.pipeline.cleaning import (
    clean_review_text,
    clean_review,
    clean_product,
    normalize_date,
    normalize_price,
    is_english,
    make_review_hash,
)


def test_clean_text_html_stripping():
    raw = "<p>This is a <strong>great</strong> supplement!</p><br/>"
    cleaned = clean_review_text(raw)
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert "This is a great supplement!" in cleaned


def test_clean_text_whitespace_normalization():
    raw = "   Too   many    spaces   and\n\n\nline breaks\t\there.   "
    cleaned = clean_review_text(raw)
    assert cleaned == "Too many spaces and line breaks here."


def test_clean_text_control_characters():
    raw = "Clean \x00this \x08text \x1fwith \x0bcontrols"
    cleaned = clean_review_text(raw)
    assert cleaned == "Clean this text with controls"


def test_clean_review_short_rejection():
    # Less than 5 characters should be rejected (returns None)
    raw = {"text": "Ok", "rating": 5}
    assert clean_review(raw, product_id=1) is None

    raw_empty = {"text": "", "rating": 4}
    assert clean_review(raw_empty, product_id=1) is None

    raw_spaces = {"text": "    ", "rating": 4}
    assert clean_review(raw_spaces, product_id=1) is None


def test_clean_review_valid():
    raw = {
        "text": "<b>Loved</b> this product so much!",
        "rating": 5,
        "author": "  John Doe  ",
        "date": "2026-03-15",
    }
    cleaned = clean_review(raw, product_id=42)
    assert cleaned is not None
    assert cleaned["product_id"] == 42
    assert cleaned["raw_text"] == "<b>Loved</b> this product so much!"
    assert cleaned["cleaned_text"] == "Loved this product so much!"
    assert cleaned["author"] == "John Doe"
    assert cleaned["rating"] == 5
    assert cleaned["review_date"] == date(2026, 3, 15)
    assert "text_hash" in cleaned
    assert len(cleaned["text_hash"]) == 64  # SHA-256 hex string


def test_parse_date_formats():
    assert normalize_date("2026-01-15") == date(2026, 1, 15)
    assert normalize_date("15/01/2026") == date(2026, 1, 15)
    assert normalize_date("Jan 15, 2026") == date(2026, 1, 15)
    assert normalize_date("15 Jan 2026") == date(2026, 1, 15)
    assert normalize_date("invalid-date-string") is None
    assert normalize_date(None) is None


def test_parse_price_formats():
    assert normalize_price("₹1,499.00") == 1499.00
    assert normalize_price("$29.99") == 29.99
    assert normalize_price("1,200") == 1200.00
    assert normalize_price(850) == 850.0
    assert normalize_price("Free") is None
    assert normalize_price(None) is None


def test_language_filtering():
    english_text = "This supplement really improved my sleep quality."
    non_english_text = "यह उत्पाद बहुत अच्छा है और मुझे बहुत फायदा हुआ।"
    assert is_english(english_text) is True
    assert is_english(non_english_text) is False


def test_clean_product():
    raw = {
        "name": "  Natural Vitamin C 1000mg  ",
        "url": "https://example.com/vit-c",
        "price": "Rs. 499.00",
        "description": "<div>Immunity booster</div>",
        "image_url": "https://example.com/img.jpg",
    }
    prod = clean_product(raw)
    assert prod["name"] == "Natural Vitamin C 1000mg"
    assert prod["price"] == 499.0
    assert prod["description"] == "Immunity booster"
    assert prod["url"] == "https://example.com/vit-c"
