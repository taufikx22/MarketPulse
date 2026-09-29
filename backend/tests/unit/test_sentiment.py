from app.pipeline.sentiment import classify_sentiment, _keyword_sentiment


def test_keyword_sentiment_positive():
    text = "Absolutely love this supplement! Excellent quality and great results."
    res = _keyword_sentiment(text)
    assert res["label"] == "positive"
    assert res["score"] > 0.5


def test_keyword_sentiment_negative():
    text = "Horrible experience. Terrible taste, waste of money and scam."
    res = _keyword_sentiment(text)
    assert res["label"] == "negative"
    assert res["score"] > 0.5


def test_keyword_sentiment_neutral():
    text = "The bottle arrived on Tuesday."
    res = _keyword_sentiment(text)
    assert res["label"] == "neutral"
    assert res["score"] == 0.5


def test_classify_sentiment_stable_schema():
    sample_texts = [
        "Works really well for my daily recovery.",
        "Disappointed with the product.",
        "Standard packaging.",
    ]
    for text in sample_texts:
        res = classify_sentiment(text)
        assert isinstance(res, dict)
        assert "label" in res
        assert "score" in res
        assert res["label"] in ("positive", "negative", "neutral")
        assert 0.0 <= res["score"] <= 1.0


def test_classify_sentiment_fallback_on_model_absence(monkeypatch):
    """Verify that when HF pipeline is None, it safely uses keyword fallback."""
    import app.pipeline.sentiment as sentiment_module
    monkeypatch.setattr(sentiment_module, "_pipeline", None)
    monkeypatch.setattr(sentiment_module, "_use_fallback", True)

    res = sentiment_module.classify_sentiment("Amazing supplement, wonderful benefits")
    assert res["label"] == "positive"
    assert res["score"] > 0.5
