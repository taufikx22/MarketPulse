from fastapi import APIRouter, Query, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.review import Review
from app.pipeline.embeddings import search_reviews

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def semantic_search(
    q: str = Query(..., min_length=2),
    n: int = Query(10, le=50),
    brand_id: int = Query(None),
    sentiment: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if brand_id:
        filters.append({"brand_id": brand_id})
    if sentiment:
        filters.append({"sentiment": sentiment})

    where = None
    if len(filters) == 1:
        where = filters[0]
    elif len(filters) > 1:
        where = {"$and": filters}

    hits = search_reviews(q, n_results=n, where=where)
    if not hits:
        return {"query": q, "results": []}

    # Fetch additional review info from Database
    review_ids = [h["metadata"].get("review_id") for h in hits if h["metadata"].get("review_id")]
    
    enriched_map = {}
    if review_ids:
        result = await db.execute(
            select(Review)
            .options(selectinload(Review.product))
            .where(Review.id.in_(review_ids))
        )
        for r in result.scalars().all():
            enriched_map[r.id] = {
                "product_name": r.product.name if r.product else "Generic Product",
                "author": r.author or "Anonymous",
                "date": str(r.review_date) if r.review_date else None,
                "rating": r.rating,
            }

    results = []
    for h in hits:
        rid = h["metadata"].get("review_id")
        extra = enriched_map.get(rid, {})
        results.append({
            "review_id": rid,
            "text": h["document"],
            "sentiment": h["metadata"].get("sentiment"),
            "distance": h.get("distance"),
            "product_name": extra.get("product_name"),
            "author": extra.get("author"),
            "date": extra.get("date"),
            "rating": extra.get("rating"),
        })

    return {
        "query": q,
        "results": results,
    }

