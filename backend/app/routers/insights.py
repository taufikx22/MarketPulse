from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.insight import Insight
from app.schemas import EnrichedInsightOut
from app.models.review import Review

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=list[EnrichedInsightOut])
async def list_insights(
    brand_id: int = Query(None),
    type: str = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    q = select(Insight)
    if brand_id:
        q = q.where(Insight.brand_id == brand_id)
    if type:
        q = q.where(Insight.type == type)
    q = q.order_by(Insight.generated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    insights = result.scalars().all()

    enriched_insights = []
    for insight in insights:
        reviews = []
        if insight.supporting_review_ids:
            import json
            # Handle SQLite list parsing if it's stored as JSON string
            if isinstance(insight.supporting_review_ids, str):
                try:
                    r_ids = json.loads(insight.supporting_review_ids)
                except Exception:
                    r_ids = []
            else:
                r_ids = list(insight.supporting_review_ids)

            if r_ids:
                res_reviews = await db.execute(
                    select(Review).where(Review.id.in_(r_ids))
                )
                reviews = res_reviews.scalars().all()

        enriched_insights.append({
            "id": insight.id,
            "brand_id": insight.brand_id,
            "type": insight.type,
            "text": insight.text,
            "generated_at": insight.generated_at,
            "supporting_review_ids": r_ids if 'r_ids' in locals() else [],
            "supporting_reviews": reviews
        })
    return enriched_insights

