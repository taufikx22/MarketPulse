import hashlib
import re
from datetime import date, datetime
from typing import Optional
from bs4 import BeautifulSoup


def clean_review_text(raw: str) -> str:
    """Strip HTML artifacts, collapse whitespace, remove control characters."""
    text = BeautifulSoup(raw, "lxml").get_text() if "<" in raw else raw
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_date(date_str: Optional[str]) -> Optional[date]:
    """Try several common date formats. Returns None if unparseable."""
    if not date_str:
        return None
    date_str = date_str.strip()
    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%b %d, %Y", "%B %d, %Y",
        "%d %b %Y", "%d %B %Y", "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def normalize_price(price_val) -> Optional[float]:
    if price_val is None:
        return None
    if isinstance(price_val, (int, float)):
        return round(float(price_val), 2)
    cleaned = re.sub(r"[^\d.]", "", str(price_val))
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def make_review_hash(text: str, product_id: int) -> str:
    normalized = text.strip().lower()
    return hashlib.sha256(f"{normalized}:{product_id}".encode()).hexdigest()


def is_english(text: str) -> bool:
    """Quick heuristic: if more than 70% of characters are ASCII letters/spaces, treat as English.
    Not a real language detector, but good enough to flag obvious non-English reviews."""
    if not text:
        return False
    ascii_chars = sum(1 for c in text if c.isascii())
    return (ascii_chars / len(text)) > 0.7


def clean_product(raw: dict) -> dict:
    return {
        "name": raw.get("name", "").strip(),
        "url": raw.get("url", "").strip(),
        "price": normalize_price(raw.get("price")),
        "description": clean_review_text(raw.get("description", "")),
        "image_url": raw.get("image_url"),
    }


def clean_review(raw: dict, product_id: int) -> Optional[dict]:
    """Clean a single raw review dict. Returns None if the review should be dropped."""
    text = raw.get("text", "")
    if not text or len(text.strip()) < 5:
        return None

    cleaned = clean_review_text(text)
    if not is_english(cleaned):
        return None

    return {
        "product_id": product_id,
        "raw_text": text,
        "cleaned_text": cleaned,
        "rating": raw.get("rating"),
        "author": (raw.get("author") or "").strip()[:255] or None,
        "review_date": normalize_date(raw.get("date")),
        "text_hash": make_review_hash(cleaned, product_id),
    }
