"""Generate analytical insights for tracked brands.
Usage: python -m app.pipeline.insights
"""

import asyncio
import json
from collections import defaultdict, Counter
from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.database import async_session
from app.models.brand import Brand
from app.models.product import Product
from app.models.review import Review
from app.models.analysis import ReviewAnalysis
from app.models.insight import Insight


def parse_themes(themes_val):
    if not themes_val:
        return []
    if isinstance(themes_val, str):
        try:
            return json.loads(themes_val)
        except Exception:
            return []
    return list(themes_val)


async def generate_brand_insights(brand_id: int, session):
    """Analyze a single brand and write insights into the database."""
    # Fetch brand
    brand = await session.get(Brand, brand_id)
    if not brand:
        return

    # Clear existing insights for this brand to prevent duplicates
    await session.execute(
        delete(Insight).where(Insight.brand_id == brand_id)
    )
    await session.flush()

    # Query reviews and analyses
    result = await session.execute(
        select(Review, ReviewAnalysis)
        .join(Product, Product.id == Review.product_id)
        .join(ReviewAnalysis, ReviewAnalysis.review_id == Review.id)
        .where(Product.brand_id == brand_id)
    )
    rows = result.all()

    if not rows:
        # Create a default neutral onboarding insight
        default_insight = Insight(
            brand_id=brand_id,
            type="neutral",
            text=f"MarketPulse has started tracking {brand.name}. Feed review data or run a scrape to generate customer experience analytics.",
            supporting_review_ids=[]
        )
        session.add(default_insight)
        await session.flush()
        return

    # Aggregators
    total_reviews = len(rows)
    ratings = []
    theme_sentiments = defaultdict(list)  # theme -> list of (sentiment_label, review_id)
    all_themes = []

    for review, analysis in rows:
        if review.rating is not None:
            ratings.append(review.rating)
        
        themes = parse_themes(analysis.themes)
        all_themes.extend(themes)
        
        for t in themes:
            theme_sentiments[t].append((analysis.sentiment, review.id))

    avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
    theme_counts = Counter(all_themes)
    top_themes = theme_counts.most_common(3)

    insights_generated = 0

    # 1. Analyze sentiment per theme
    for theme, items in theme_sentiments.items():
        if len(items) < 3:
            continue
        
        positives = [it[1] for it in items if it[0] == "positive"]
        negatives = [it[1] for it in items if it[0] == "negative"]
        total_theme_mentions = len(items)
        
        neg_ratio = len(negatives) / total_theme_mentions
        pos_ratio = len(positives) / total_theme_mentions

        # Case A: Highly negative mentions (e.g. > 50% negative)
        if neg_ratio >= 0.5:
            text = f"Customer reviews regarding '{theme}' are significantly negative ({int(neg_ratio * 100)}% negative) for {brand.name}. Complaints frequently note quality, delays, or performance issues."
            supporting = negatives[:3]
            insight = Insight(
                brand_id=brand_id,
                type="negative_trend",
                text=text,
                supporting_review_ids=supporting
            )
            session.add(insight)
            insights_generated += 1

        # Case B: Highly positive mentions (e.g. > 75% positive)
        elif pos_ratio >= 0.75:
            text = f"'{theme.capitalize()}' is highlighted as a major competitive strength for {brand.name}, receiving {int(pos_ratio * 100)}% positive customer sentiment."
            supporting = positives[:3]
            insight = Insight(
                brand_id=brand_id,
                type="positive_trend",
                text=text,
                supporting_review_ids=supporting
            )
            session.add(insight)
            insights_generated += 1

    # 2. General brand status summary if low review count or no specific themes triggered insights
    if insights_generated == 0 or total_reviews >= 5:
        top_theme_name = top_themes[0][0] if top_themes else "general experience"
        summary_text = (
            f"{brand.name} maintains an average customer rating of {avg_rating:.1f}/5 stars across "
            f"{total_reviews} reviews. Conversations are heavily focused on '{top_theme_name}' topics."
        )
        # Select 3 recent reviews
        recent_review_ids = [r[0].id for r in rows[-3:]]
        summary_insight = Insight(
            brand_id=brand_id,
            type="neutral",
            text=summary_text,
            supporting_review_ids=recent_review_ids
        )
        session.add(summary_insight)

    await session.commit()
    print(f"Generated insights for {brand.name}.")


async def generate_all_insights():
    async with async_session() as session:
        result = await session.execute(select(Brand))
        brands = result.scalars().all()
        for brand in brands:
            await generate_brand_insights(brand.id, session)


if __name__ == "__main__":
    asyncio.run(generate_all_insights())
