import json
from datetime import date, datetime
import pytest
from app.models.brand import Brand
from app.models.product import Product
from app.models.review import Review
from app.models.analysis import ReviewAnalysis
from app.pipeline.anomalies import detect_brand_anomalies


@pytest.mark.asyncio
async def test_insufficient_data_anomaly_state(db_session):
    """Brands with fewer than 6 reviews return an explicit insufficient_data state."""
    brand = Brand(name="Early Stage Brand", url="https://early.test", category="wellness")
    db_session.add(brand)
    await db_session.flush()

    prod = Product(brand_id=brand.id, name="Test Prod", url="https://early.test/p1")
    db_session.add(prod)
    await db_session.flush()

    # Seed only 3 reviews
    for i in range(3):
        rev = Review(product_id=prod.id, raw_text=f"Review text {i}", rating=5, text_hash=f"e_{i}")
        db_session.add(rev)
        await db_session.flush()
        analysis = ReviewAnalysis(review_id=rev.id, sentiment="positive", sentiment_score=0.9, themes="[]")
        db_session.add(analysis)

    await db_session.commit()

    anomalies = await detect_brand_anomalies(brand.id, db_session)
    assert len(anomalies) == 1
    assert anomalies[0].type == "insufficient_data"
    assert anomalies[0].status == "insufficient_data"
    assert anomalies[0].severity == "low"
    assert "minimum 6 required" in anomalies[0].text


@pytest.mark.asyncio
async def test_negative_sentiment_spike(db_session):
    """Detect negative sentiment spike when current negative ratio exceeds baseline by >= 15 pp."""
    brand = Brand(name="Spike Brand", url="https://spike.test", category="wellness")
    db_session.add(brand)
    await db_session.flush()

    prod = Product(brand_id=brand.id, name="Spike Product", url="https://spike.test/prod")
    db_session.add(prod)
    await db_session.flush()

    # Baseline period: 4 positive reviews, 0 negative (0% negative)
    for i in range(4):
        rev = Review(
            product_id=prod.id,
            raw_text=f"Baseline good review {i}",
            rating=5,
            review_date=date(2026, 1, 1 + i),
            text_hash=f"b_pos_{i}",
        )
        db_session.add(rev)
        await db_session.flush()
        db_session.add(ReviewAnalysis(review_id=rev.id, sentiment="positive", sentiment_score=0.9, themes="[]"))

    # Current period: 1 positive review, 3 negative reviews (75% negative)
    for i in range(3):
        rev = Review(
            product_id=prod.id,
            raw_text=f"Current bad review {i}",
            rating=1,
            review_date=date(2026, 2, 10 + i),
            text_hash=f"c_neg_{i}",
        )
        db_session.add(rev)
        await db_session.flush()
        db_session.add(ReviewAnalysis(review_id=rev.id, sentiment="negative", sentiment_score=0.1, themes="[]"))

    rev_pos = Review(
        product_id=prod.id,
        raw_text="Current one good review",
        rating=4,
        review_date=date(2026, 2, 15),
        text_hash="c_pos_1",
    )
    db_session.add(rev_pos)
    await db_session.flush()
    db_session.add(ReviewAnalysis(review_id=rev_pos.id, sentiment="positive", sentiment_score=0.8, themes="[]"))

    await db_session.commit()

    anomalies = await detect_brand_anomalies(brand.id, db_session)
    spike_anoms = [a for a in anomalies if a.type == "negative_sentiment_spike"]
    assert len(spike_anoms) == 1
    anom = spike_anoms[0]
    assert anom.metric == "negative_sentiment_pct"
    assert anom.deviation >= 15.0  # +75 pp vs 0 pp
    assert "Negative sentiment increased" in anom.text
    assert len(anom.supporting_review_ids) > 0


@pytest.mark.asyncio
async def test_rating_deterioration(db_session):
    """Detect drop in rating when current average drops >= 0.5 stars relative to baseline."""
    brand = Brand(name="Drop Brand", url="https://drop.test", category="wellness")
    db_session.add(brand)
    await db_session.flush()

    prod = Product(brand_id=brand.id, name="Drop Product", url="https://drop.test/prod")
    db_session.add(prod)
    await db_session.flush()

    # Baseline: 4 reviews all 5 stars (avg 5.0)
    for i in range(4):
        rev = Review(
            product_id=prod.id,
            raw_text=f"Great {i}",
            rating=5,
            review_date=date(2026, 1, 1 + i),
            text_hash=f"d_b_{i}",
        )
        db_session.add(rev)
        await db_session.flush()
        db_session.add(ReviewAnalysis(review_id=rev.id, sentiment="positive", sentiment_score=0.9, themes="[]"))

    # Current: 4 reviews all 2 stars (avg 2.0, drop of 3.0 stars)
    for i in range(4):
        rev = Review(
            product_id=prod.id,
            raw_text=f"Poor quality {i}",
            rating=2,
            review_date=date(2026, 2, 1 + i),
            text_hash=f"d_c_{i}",
        )
        db_session.add(rev)
        await db_session.flush()
        db_session.add(ReviewAnalysis(review_id=rev.id, sentiment="negative", sentiment_score=0.2, themes="[]"))

    await db_session.commit()

    anomalies = await detect_brand_anomalies(brand.id, db_session)
    drop_anoms = [a for a in anomalies if a.type == "rating_deterioration"]
    assert len(drop_anoms) == 1
    anom = drop_anoms[0]
    assert anom.deviation <= -0.50
    assert "Average customer rating dropped" in anom.text


@pytest.mark.asyncio
async def test_theme_complaint_spike(db_session):
    """Detect specific theme complaint surge in current period."""
    brand = Brand(name="Theme Spike Brand", url="https://themespike.test", category="wellness")
    db_session.add(brand)
    await db_session.flush()

    prod = Product(brand_id=brand.id, name="Theme Prod", url="https://themespike.test/prod")
    db_session.add(prod)
    await db_session.flush()

    # Baseline: 4 reviews, no packaging complaints
    for i in range(4):
        rev = Review(
            product_id=prod.id,
            raw_text=f"Good {i}",
            rating=5,
            review_date=date(2026, 1, 1 + i),
            text_hash=f"th_b_{i}",
        )
        db_session.add(rev)
        await db_session.flush()
        db_session.add(ReviewAnalysis(review_id=rev.id, sentiment="positive", sentiment_score=0.9, themes=json.dumps(["efficacy"])))

    # Current: 4 reviews, 3 packaging complaints
    for i in range(3):
        rev = Review(
            product_id=prod.id,
            raw_text=f"Broken seal packaging {i}",
            rating=1,
            review_date=date(2026, 2, 1 + i),
            text_hash=f"th_c_{i}",
        )
        db_session.add(rev)
        await db_session.flush()
        db_session.add(ReviewAnalysis(review_id=rev.id, sentiment="negative", sentiment_score=0.1, themes=json.dumps(["packaging"])))

    rev_neutral = Review(
        product_id=prod.id,
        raw_text="Average taste",
        rating=3,
        review_date=date(2026, 2, 5),
        text_hash="th_c_neutral",
    )
    db_session.add(rev_neutral)
    await db_session.flush()
    db_session.add(ReviewAnalysis(review_id=rev_neutral.id, sentiment="neutral", sentiment_score=0.5, themes=json.dumps(["taste/flavor"])))

    await db_session.commit()

    anomalies = await detect_brand_anomalies(brand.id, db_session)
    theme_anoms = [a for a in anomalies if a.type == "theme_complaint_spike"]
    assert len(theme_anoms) >= 1
    anom = next(a for a in theme_anoms if "packaging" in a.text)
    assert "packaging" in anom.metric
    assert anom.severity == "high"


@pytest.mark.asyncio
async def test_no_anomaly_when_metrics_stable(db_session):
    """Verify that when metrics remain stable between baseline and current, no false anomalies are triggered."""
    brand = Brand(name="Stable Brand", url="https://stable.test", category="wellness")
    db_session.add(brand)
    await db_session.flush()

    prod = Product(brand_id=brand.id, name="Stable Prod", url="https://stable.test/prod")
    db_session.add(prod)
    await db_session.flush()

    # 8 consistently positive reviews across both periods
    for i in range(8):
        rev = Review(
            product_id=prod.id,
            raw_text=f"Consistently high quality supplement {i}",
            rating=5,
            review_date=date(2026, 1, 1 + i),
            text_hash=f"st_{i}",
        )
        db_session.add(rev)
        await db_session.flush()
        db_session.add(ReviewAnalysis(review_id=rev.id, sentiment="positive", sentiment_score=0.9, themes=json.dumps(["efficacy"])))

    await db_session.commit()

    anomalies = await detect_brand_anomalies(brand.id, db_session)
    # No negative spike, rating drop, or theme spike should be triggered
    active_anomalies = [a for a in anomalies if a.type != "insufficient_data"]
    assert len(active_anomalies) == 0
