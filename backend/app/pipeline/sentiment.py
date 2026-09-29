"""Sentiment classification for reviews.
Uses HuggingFace's cardiffnlp model when available, falls back to a
keyword-based scoring approach for lightweight environments without torch/GPU."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_pipeline = None
_use_fallback = False


def _load_model():
    global _pipeline, _use_fallback
    if _pipeline is not None or _use_fallback:
        return

    try:
        from transformers import pipeline
        _pipeline = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            max_length=512,
            truncation=True,
            model_kwargs={"local_files_only": True},
        )
        logger.info("Loaded Hugging Face sentiment model (cardiffnlp/twitter-roberta-base-sentiment-latest)")
    except Exception as exc:
        _use_fallback = True
        logger.info("Local Hugging Face sentiment model not cached; activating keyword-based fallback: %s", exc)


def classify_sentiment(text: str) -> dict:
    """Returns {"label": "positive"|"neutral"|"negative", "score": float}"""
    _load_model()

    if _pipeline is not None:
        result = _pipeline(text[:512])[0]
        label = result["label"].lower()
        # Model outputs: positive, neutral, negative
        if label not in ("positive", "neutral", "negative"):
            label = "neutral"
        return {"label": label, "score": round(result["score"], 4)}

    # Fallback: keyword-based scoring
    return _keyword_sentiment(text)


def _keyword_sentiment(text: str) -> dict:
    """Simple keyword-based sentiment when HF models aren't available."""
    text_lower = text.lower()
    pos_words = {"great", "love", "excellent", "amazing", "good", "best", "worth", "recommend", "happy", "improved", "effective", "fantastic", "perfect"}
    neg_words = {"bad", "terrible", "waste", "disappointed", "horrible", "worst", "broken", "damaged", "useless", "poor", "issue", "problem", "complaint"}

    pos_count = sum(1 for w in pos_words if w in text_lower)
    neg_count = sum(1 for w in neg_words if w in text_lower)
    total = pos_count + neg_count

    if total == 0:
        return {"label": "neutral", "score": 0.5}

    ratio = pos_count / total
    if ratio > 0.6:
        return {"label": "positive", "score": round(0.5 + ratio * 0.5, 4)}
    elif ratio < 0.4:
        return {"label": "negative", "score": round(0.5 + (1 - ratio) * 0.5, 4)}
    return {"label": "neutral", "score": 0.5}


def batch_classify(texts: list[str]) -> list[dict]:
    _load_model()
    if _pipeline is not None:
        results = _pipeline([t[:512] for t in texts], batch_size=16)
        return [
            {"label": r["label"].lower(), "score": round(r["score"], 4)}
            for r in results
        ]
    return [_keyword_sentiment(t) for t in texts]
