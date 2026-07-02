from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.brand import Brand
from app.models.product import Product
from app.models.review import Review
from app.models.analysis import ReviewAnalysis

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("")
async def compare_brands(
    brand_ids: str = Query(..., description="Comma-separated brand IDs, e.g. 1,2,3"),
    db: AsyncSession = Depends(get_db),
):
    ids = [int(x.strip()) for x in brand_ids.split(",") if x.strip().isdigit()]
    if len(ids) < 2:
        from fastapi import HTTPException
        raise HTTPException(400, "Need at least 2 brand IDs")

    comparisons = []
    for bid in ids[:5]:
        brand = await db.get(Brand, bid)
        if not brand:
            continue

        # Product count and avg price
        prod_result = await db.execute(
            select(func.count(), func.avg(Product.price))
            .where(Product.brand_id == bid)
        )
        prod_row = prod_result.one()

        # Review count and avg rating
        review_result = await db.execute(
            select(func.count(), func.avg(Review.rating))
            .join(Product, Product.id == Review.product_id)
            .where(Product.brand_id == bid)
        )
        rev_row = review_result.one()

        # Sentiment distribution
        sent_result = await db.execute(
            select(ReviewAnalysis.sentiment, func.count())
            .join(Review, Review.id == ReviewAnalysis.review_id)
            .join(Product, Product.id == Review.product_id)
            .where(Product.brand_id == bid)
            .group_by(ReviewAnalysis.sentiment)
        )
        sentiment_dist = {r[0]: r[1] for r in sent_result.all()}

        # Top themes
        if db.bind.dialect.name == "sqlite":
            theme_result = await db.execute(
                select(ReviewAnalysis.themes)
                .join(Review, Review.id == ReviewAnalysis.review_id)
                .join(Product, Product.id == Review.product_id)
                .where(Product.brand_id == bid)
            )
            import json
            from collections import Counter
            c = Counter()
            for row in theme_result.all():
                themes_str = row[0]
                if not themes_str:
                    continue
                try:
                    themes_list = json.loads(themes_str) if isinstance(themes_str, str) else themes_str
                    c.update(themes_list)
                except Exception:
                    pass
            top_themes = [{"theme": t, "count": cnt} for t, cnt in c.most_common(5)]
        else:
            theme_result = await db.execute(
                select(func.unnest(ReviewAnalysis.themes).label("theme"), func.count().label("cnt"))
                .join(Review, Review.id == ReviewAnalysis.review_id)
                .join(Product, Product.id == Review.product_id)
                .where(Product.brand_id == bid)
                .group_by("theme")
                .order_by(func.count().desc())
                .limit(5)
            )
            top_themes = [{"theme": r.theme, "count": r.cnt} for r in theme_result.all()]

        comparisons.append({
            "brand_id": bid,
            "brand_name": brand.name,
            "product_count": prod_row[0],
            "avg_price": round(float(prod_row[1] or 0), 2),
            "review_count": rev_row[0],
            "avg_rating": round(float(rev_row[1] or 0), 1),
            "sentiment": sentiment_dist,
            "top_themes": top_themes,
        })

    return comparisons
