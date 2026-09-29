import json
import pytest
from sqlalchemy import select
from app.pipeline.insights import generate_brand_insights, parse_themes
from app.models.brand import Brand
from app.models.product import Product
from app.models.review import Review
from app.models.analysis import ReviewAnalysis
from app.models.insight import Insight


def test_parse_themes():
    assert parse_themes(None) == []
    assert parse_themes("") == []
    assert parse_themes('["efficacy", "taste"]') == ["efficacy", "taste"]
    assert parse_themes(["efficacy", "price"]) == ["efficacy", "price"]
    assert parse_themes("invalid json") == []


@pytest.mark.asyncio
async def test_positive_threshold_generates_positive_trend(db_session):
    # Brand with 3 positive reviews on "efficacy"
    brand = Brand(name="Vitality Lab", url="https://vitality.test", category="energy")
    db_session.add(brand)
    await db_session.flush()

    prod = Product(brand_id=brand.id, name="Energy Ultra", url="https://vitality.test/p1", price=999.0)
    db_session.add(prod)
    await db_session.flush()

    for i in range(3):
        rev = Review(product_id=prod.id, rating=5, raw_text=f"Great effect {i}", text_hash=f"v_hash_{i}")
        db_session.add(rev)
        await db_session.flush()

        analysis = ReviewAnalysis(
            review_id=rev.id,
            sentiment="positive",
            sentiment_score=0.9,
            themes=json.dumps(["efficacy"]),
        )
        db_session.add(analysis)

    await db_session.commit()

    await generate_brand_insights(brand.id, db_session)

    res = await db_session.execute(select(Insight).where(Insight.brand_id == brand.id))
    insights = res.scalars().all()

    types = [ins.type for ins in insights]
    assert "positive_trend" in types
    pos_insight = next(ins for ins in insights if ins.type == "positive_trend")
    assert "efficacy" in pos_insight.text.lower()
    assert "strength" in pos_insight.text.lower() or "positive" in pos_insight.text.lower()


@pytest.mark.asyncio
async def test_negative_threshold_generates_negative_trend(db_session):
    # Brand with 2 negative and 1 positive review on "taste/flavor" (2/3 = 66% >= 50%)
    brand = Brand(name="Bitter Herbs", url="https://bitter.test", category="ayurveda")
    db_session.add(brand)
    await db_session.flush()

    prod = Product(brand_id=brand.id, name="Bitter Tonic", url="https://bitter.test/tonic", price=499.0)
    db_session.add(prod)
    await db_session.flush()

    sentiments = ["negative", "negative", "positive"]
    for i, s in enumerate(sentiments):
        rev = Review(product_id=prod.id, rating=2 if s == "negative" else 4, raw_text=f"Taste test {i}", text_hash=f"b_hash_{i}")
        db_session.add(rev)
        await db_session.flush()

        analysis = ReviewAnalysis(
            review_id=rev.id,
            sentiment=s,
            sentiment_score=0.2 if s == "negative" else 0.8,
            themes=json.dumps(["taste/flavor"]),
        )
        db_session.add(analysis)

    await db_session.commit()

    await generate_brand_insights(brand.id, db_session)

    res = await db_session.execute(select(Insight).where(Insight.brand_id == brand.id))
    insights = res.scalars().all()

    types = [ins.type for ins in insights]
    assert "negative_trend" in types
    neg_insight = next(ins for ins in insights if ins.type == "negative_trend")
    assert "taste/flavor" in neg_insight.text.lower()


@pytest.mark.asyncio
async def test_below_minimum_mentions_no_trend_insight(db_session):
    # Brand with only 2 reviews (below minimum requirement of 3 mentions)
    brand = Brand(name="Micro Brand", url="https://micro.test", category="skin")
    db_session.add(brand)
    await db_session.flush()

    prod = Product(brand_id=brand.id, name="Micro Cream", url="https://micro.test/cream", price=299.0)
    db_session.add(prod)
    await db_session.flush()

    for i in range(2):
        rev = Review(product_id=prod.id, rating=5, raw_text=f"Nice cream {i}", text_hash=f"m_hash_{i}")
        db_session.add(rev)
        await db_session.flush()

        analysis = ReviewAnalysis(
            review_id=rev.id,
            sentiment="positive",
            sentiment_score=0.9,
            themes=json.dumps(["efficacy"]),
        )
        db_session.add(analysis)

    await db_session.commit()

    await generate_brand_insights(brand.id, db_session)

    res = await db_session.execute(select(Insight).where(Insight.brand_id == brand.id))
    insights = res.scalars().all()

    # Should not have a positive_trend or negative_trend because mentions < 3
    types = [ins.type for ins in insights]
    assert "positive_trend" not in types
    assert "negative_trend" not in types
    # Fallback status summary insight is generated
    assert "neutral" in types
