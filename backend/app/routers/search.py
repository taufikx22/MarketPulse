from fastapi import APIRouter, Query
from app.pipeline.embeddings import search_reviews

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def semantic_search(
    q: str = Query(..., min_length=2),
    n: int = Query(10, le=50),
    brand_id: int = Query(None),
):
    where = None
    if brand_id:
        where = {"brand_id": brand_id}

    hits = search_reviews(q, n_results=n, where=where)
    return {
        "query": q,
        "results": [
            {
                "review_id": h["metadata"].get("review_id"),
                "text": h["document"][:300],
                "sentiment": h["metadata"].get("sentiment"),
                "distance": h.get("distance"),
            }
            for h in hits
        ],
    }
