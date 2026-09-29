from app.pipeline.themes import tag_themes, _keyword_themes


def test_theme_extraction_matched_keywords():
    text = "The taste and flavor is delicious, but the price is too expensive."
    themes = _keyword_themes(text)
    assert "taste/flavor" in themes
    assert "price/value" in themes


def test_theme_extraction_side_effects():
    text = "Caused severe nausea and stomach headache."
    themes = _keyword_themes(text)
    assert "side effects" in themes


def test_theme_extraction_packaging_and_shipping():
    text = "The bottle seal was broken upon delivery and courier was late."
    themes = _keyword_themes(text)
    assert "packaging" in themes or "shipping" in themes


def test_theme_extraction_fallback_default():
    text = "A nondescript item."
    themes = _keyword_themes(text)
    # When no keyword matches, fallback is ["efficacy"]
    assert themes == ["efficacy"]


def test_tag_themes_output_format():
    res = tag_themes("Noticeable stamina increase and good ingredients.")
    assert isinstance(res, list)
    assert len(res) > 0
    assert all(isinstance(t, str) for t in res)
