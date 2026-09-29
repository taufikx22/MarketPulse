from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.insight import Insight
from app.models.brand import Brand
from app.models.product import Product
from app.schemas import EnrichedInsightOut
from app.models.review import Review
from app.pipeline.anomalies import detect_brand_anomalies, detect_all_anomalies

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=list[EnrichedInsightOut])
async def list_insights(
    brand_id: Optional[int] = Query(None, description="Filter insights by brand ID"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    type: Optional[str] = Query(None, description="Filter by insight or anomaly type"),
    severity: Optional[str] = Query(None, description="Filter by severity: critical, high, medium, low"),
    status: Optional[str] = Query(None, description="Filter by status: active, resolved, insufficient_data"),
    is_anomaly: Optional[bool] = Query(None, description="If true, only return anomaly/control engine records"),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    q = select(Insight)
    if brand_id is not None:
        q = q.where(Insight.brand_id == brand_id)
    if product_id is not None:
        q = q.where(Insight.product_id == product_id)
    if type:
        q = q.where(Insight.type == type)
    if severity:
        q = q.where(Insight.severity == severity)
    if status:
        q = q.where(Insight.status == status)
    if is_anomaly is True:
        q = q.where(Insight.metric.is_not(None))
    elif is_anomaly is False:
        q = q.where(Insight.metric.is_(None))

    q = q.order_by(Insight.generated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    insights = result.scalars().all()

    enriched_insights = []
    for insight in insights:
        reviews = []
        r_ids = []
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
            "product_id": insight.product_id,
            "type": insight.type,
            "text": insight.text,
            "severity": insight.severity or "medium",
            "status": insight.status or "active",
            "metric": insight.metric,
            "baseline_value": insight.baseline_value,
            "current_value": insight.current_value,
            "deviation": insight.deviation,
            "threshold": insight.threshold,
            "generated_at": insight.generated_at,
            "supporting_review_ids": r_ids,
            "supporting_reviews": reviews
        })
    return enriched_insights


@router.post("/detect-anomalies")
async def trigger_anomaly_detection(
    brand_id: Optional[int] = Query(None, description="Optional brand ID; if omitted, runs for all brands"),
    db: AsyncSession = Depends(get_db),
):
    """Trigger statistical control / anomaly detection rules on ingested brand review data."""
    if brand_id is not None:
        brand = await db.get(Brand, brand_id)
        if not brand:
            raise HTTPException(404, f"Brand with ID {brand_id} not found.")
        anomalies = await detect_brand_anomalies(brand_id, db)
    else:
        anomalies = await detect_all_anomalies(session=db)

    return {
        "status": "success",
        "anomalies_detected": len(anomalies),
        "anomalies": [
            {
                "id": a.id,
                "brand_id": a.brand_id,
                "type": a.type,
                "severity": a.severity,
                "metric": a.metric,
                "deviation": a.deviation,
                "explanation": a.text,
            }
            for a in anomalies
        ],
    }

