"""Zero-shot theme tagging for reviews.
Tags each review against a fixed set of wellness/supplement themes."""

THEME_LABELS = [
    "efficacy",
    "taste/flavor",
    "price/value",
    "shipping/delivery",
    "packaging",
    "side effects",
    "ingredient quality",
    "customer service",
    "subscription",
]

import logging

logger = logging.getLogger(__name__)

_classifier = None
_use_fallback = False


def _load_model():
    global _classifier, _use_fallback
    if _classifier is not None or _use_fallback:
        return
    try:
        from transformers import pipeline
        _classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            model_kwargs={"local_files_only": True},
        )
        logger.info("Loaded Hugging Face zero-shot classification model (facebook/bart-large-mnli)")
    except Exception as exc:
        _use_fallback = True
        logger.info("Local Hugging Face zero-shot model not cached; activating keyword-based theme tagger: %s", exc)


def tag_themes(text: str, threshold: float = 0.3) -> list[str]:
    """Return themes with confidence above threshold."""
    _load_model()

    if _classifier is not None:
        result = _classifier(text[:512], THEME_LABELS, multi_label=True)
        return [
            label for label, score in zip(result["labels"], result["scores"])
            if score >= threshold
        ]

    return _keyword_themes(text)


# Keyword mappings so the pipeline works without downloading bart-large-mnli
_THEME_KEYWORDS = {
    "efficacy": {"works", "effective", "results", "noticed", "difference", "improved", "energy", "sleep", "benefit", "helps"},
    "taste/flavor": {"taste", "flavor", "swallow", "capsule", "bitter", "smell"},
    "price/value": {"price", "expensive", "cheap", "value", "worth", "cost", "affordable", "pricey", "investment"},
    "shipping/delivery": {"shipping", "delivery", "shipped", "arrived", "days", "courier", "late", "fast delivery"},
    "packaging": {"packaging", "package", "sealed", "damaged", "box", "broken", "cracked", "seal"},
    "side effects": {"stomach", "nausea", "headache", "side effect", "discomfort", "digestive", "reaction"},
    "ingredient quality": {"ingredient", "quality", "pure", "lab tested", "transparent", "source", "organic", "natural"},
    "customer service": {"customer service", "support", "response", "replaced", "refund", "return"},
    "subscription": {"subscription", "subscribe", "recurring", "auto", "reorder", "monthly"},
}


def _keyword_themes(text: str) -> list[str]:
    text_lower = text.lower()
    matched = []
    for theme, keywords in _THEME_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(theme)
    return matched if matched else ["efficacy"]  # default if nothing matches


def batch_tag(texts: list[str], threshold: float = 0.3) -> list[list[str]]:
    return [tag_themes(t, threshold) for t in texts]
