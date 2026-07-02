from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.insight import Insight
from app.schemas import InsightOut

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=list[InsightOut])
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
    return result.scalars().all()
