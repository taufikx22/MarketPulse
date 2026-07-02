"""Run NLP enrichment on all un-analyzed reviews.
Usage: python -m app.pipeline.enrich"""

import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import async_session
from app.models.review import Review
from app.models.analysis import ReviewAnalysis
from app.pipeline.sentiment import classify_sentiment
from app.pipeline.themes import tag_themes
from app.pipeline.embeddings import upsert_review


async def enrich_reviews():
    async with async_session() as session:
        # Find reviews that don't have analysis yet
        result = await session.execute(
            select(Review)
            .options(selectinload(Review.product))
            .outerjoin(ReviewAnalysis)
            .where(ReviewAnalysis.id.is_(None))
        )
        reviews = result.scalars().all()

        if not reviews:
            print("No un-analyzed reviews found.")
            return

        print(f"Enriching {len(reviews)} reviews...")

        for i, review in enumerate(reviews):
            text = review.cleaned_text or review.raw_text

            # Sentiment
            sent = classify_sentiment(text)

            # Themes
            themes = tag_themes(text)

            # Embedding
            product = review.product
            brand_id = product.brand_id if product else None
            embedding_id = upsert_review(
                review.id, text,
                metadata={
                    "product_id": review.product_id,
                    "brand_id": brand_id or 0,
                    "sentiment": sent["label"],
                    "rating": review.rating or 0,
                },
            )

            import json
            db_themes = json.dumps(themes) if session.bind.dialect.name == "sqlite" else themes

            analysis = ReviewAnalysis(
                review_id=review.id,
                sentiment=sent["label"],
                sentiment_score=sent["score"],
                themes=db_themes,
                embedding_id=embedding_id,
            )
            session.add(analysis)

            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(reviews)}")

        await session.commit()
        print(f"Done. Enriched {len(reviews)} reviews.")


if __name__ == "__main__":
    asyncio.run(enrich_reviews())
