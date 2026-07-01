from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.brand import Brand
from app.models.product import Product
from app.models.review import Review
from app.models.analysis import ReviewAnalysis
from app.schemas import BrandOut, ProductOut, ReviewOut

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("", response_model=list[BrandOut])
async def list_brands(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Brand).order_by(Brand.name))
    return result.scalars().all()


@router.get("/{brand_id}", response_model=BrandOut)
async def get_brand(brand_id: int, db: AsyncSession = Depends(get_db)):
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.get("/{brand_id}/products", response_model=list[ProductOut])
async def list_products(brand_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product).where(Product.brand_id == brand_id).order_by(Product.name)
    )
    return result.scalars().all()


@router.get("/{brand_id}/reviews", response_model=list[ReviewOut])
async def list_reviews(
    brand_id: int,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review)
        .join(Product, Product.id == Review.product_id)
        .where(Product.brand_id == brand_id)
        .order_by(Review.review_date.desc().nullslast())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.get("/{brand_id}/sentiment-trend")
async def sentiment_trend(brand_id: int, db: AsyncSession = Depends(get_db)):
    """Weekly sentiment aggregation for a brand's reviews."""
    result = await db.execute(
        select(
            func.date_trunc("week", Review.review_date).label("week"),
            ReviewAnalysis.sentiment,
            func.count().label("count"),
            func.avg(ReviewAnalysis.sentiment_score).label("avg_score"),
        )
        .join(Product, Product.id == Review.product_id)
        .join(ReviewAnalysis, ReviewAnalysis.review_id == Review.id)
        .where(Product.brand_id == brand_id)
        .group_by("week", ReviewAnalysis.sentiment)
        .order_by("week")
    )
    rows = result.all()
    return [
        {"week": str(r.week), "sentiment": r.sentiment, "count": r.count, "avg_score": round(float(r.avg_score), 3)}
        for r in rows
    ]


@router.get("/{brand_id}/themes")
async def theme_breakdown(brand_id: int, db: AsyncSession = Depends(get_db)):
    """Theme frequency with average sentiment score per theme."""
    result = await db.execute(
        select(
            func.unnest(ReviewAnalysis.themes).label("theme"),
            func.count().label("count"),
            func.avg(ReviewAnalysis.sentiment_score).label("avg_score"),
        )
        .join(Review, Review.id == ReviewAnalysis.review_id)
        .join(Product, Product.id == Review.product_id)
        .where(Product.brand_id == brand_id)
        .group_by("theme")
        .order_by(func.count().desc())
    )
    rows = result.all()
    return [
        {"theme": r.theme, "count": r.count, "avg_score": round(float(r.avg_score), 3)}
        for r in rows
    ]
