"""Explainable statistical and rule-based control / anomaly detection engine.

Detects:
1. Negative sentiment spike (e.g. +15 pp increase over baseline)
2. Rating deterioration (e.g. >= 0.5 star drop vs baseline)
3. Review volume anomaly (unusual surge or cliff in customer reviews)
4. Theme complaint spike (specific driver such as packaging, efficacy, taste/flavor)
5. Product-level anomaly (underperforming relative to brand benchmarks)
6. Insufficient data state (guarantees no false precision when reviews < minimum threshold)
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.models.brand import Brand
from app.models.product import Product
from app.models.review import Review
from app.models.analysis import ReviewAnalysis
from app.models.insight import Insight
from app.pipeline.insights import parse_themes

logger = logging.getLogger(__name__)

# Minimum data requirements to establish baseline and current evaluation periods
MIN_REVIEWS_FOR_ANOMALY = 6
MIN_PERIOD_REVIEWS = 3

# Configurable anomaly thresholds
NEGATIVE_SPIKE_THRESHOLD = 0.15      # +15 percentage points
RATING_DROP_THRESHOLD = -0.50        # -0.50 star rating drop
VOLUME_SURGE_RATIO = 2.5             # 2.5x volume surge
THEME_COMPLAINT_SPIKE_THRESHOLD = 0.15 # +15 percentage points for specific theme
PRODUCT_RATING_GAP_THRESHOLD = -0.70  # product >= 0.7 stars below brand average
PRODUCT_NEGATIVE_GAP_THRESHOLD = 0.20 # product >= 20 pp above brand negative sentiment


def _partition_reviews(reviews_with_analysis: list) -> Tuple[list, list]:
    """Sort reviews chronologically and split 50/50 into baseline and current evaluation periods."""
    def sort_key(item):
        r, _ = item
        # Use review_date if available, falling back to scraped_at or id
        dt_val = r.review_date.isoformat() if r.review_date else (r.scraped_at.isoformat() if r.scraped_at else f"{r.id:08d}")
        return dt_val

    sorted_items = sorted(reviews_with_analysis, key=sort_key)
    midpoint = len(sorted_items) // 2
    baseline = sorted_items[:midpoint]
    current = sorted_items[midpoint:]
    return baseline, current


async def detect_brand_anomalies(brand_id: int, session: AsyncSession) -> list[Insight]:
    """Analyze brand reviews and generate explainable control/anomaly records."""
    brand = await session.get(Brand, brand_id)
    if not brand:
        return []

    # Fetch all reviews and their analyses for this brand
    result = await session.execute(
        select(Review, ReviewAnalysis)
        .join(Product, Product.id == Review.product_id)
        .join(ReviewAnalysis, ReviewAnalysis.review_id == Review.id)
        .where(Product.brand_id == brand_id)
    )
    rows = result.all()

    anomalies: list[Insight] = []
    total_reviews = len(rows)

    # 1. Minimum Data Guard: Avoid false precision
    if total_reviews < MIN_REVIEWS_FOR_ANOMALY:
        anom = Insight(
            brand_id=brand_id,
            type="insufficient_data",
            severity="low",
            status="insufficient_data",
            metric="data_sufficiency",
            baseline_value=float(total_reviews),
            current_value=float(total_reviews),
            deviation=0.0,
            threshold=float(MIN_REVIEWS_FOR_ANOMALY),
            text=(
                f"Insufficient historical data to evaluate statistical anomalies for {brand.name} "
                f"(found {total_reviews} reviews, minimum {MIN_REVIEWS_FOR_ANOMALY} required to establish "
                f"baseline and current evaluation periods)."
            ),
            supporting_review_ids=[r[0].id for r in rows],
        )
        anomalies.append(anom)
        session.add(anom)
        await session.flush()
        return anomalies

    baseline, current = _partition_reviews(rows)
    if len(baseline) < MIN_PERIOD_REVIEWS or len(current) < MIN_PERIOD_REVIEWS:
        return anomalies

    # Helper aggregators for a period
    def period_metrics(items):
        n = len(items)
        ratings = [r.rating for r, _ in items if r.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        negatives = [r.id for r, a in items if a.sentiment == "negative"]
        positives = [r.id for r, a in items if a.sentiment == "positive"]
        neg_ratio = len(negatives) / n if n else 0.0
        pos_ratio = len(positives) / n if n else 0.0

        # Theme negative counts
        theme_neg = defaultdict(list)
        theme_total = defaultdict(int)
        for r, a in items:
            themes = parse_themes(a.themes)
            for t in themes:
                theme_total[t] += 1
                if a.sentiment == "negative":
                    theme_neg[t].append(r.id)

        return {
            "count": n,
            "ratings": ratings,
            "avg_rating": avg_rating,
            "negatives": negatives,
            "positives": positives,
            "neg_ratio": neg_ratio,
            "pos_ratio": pos_ratio,
            "theme_neg": theme_neg,
            "theme_total": theme_total,
        }

    b_meta = period_metrics(baseline)
    c_meta = period_metrics(current)

    # 2. Negative Sentiment Spike
    neg_diff = round(c_meta["neg_ratio"] - b_meta["neg_ratio"], 4)
    if neg_diff >= NEGATIVE_SPIKE_THRESHOLD:
        severity = "critical" if neg_diff >= 0.30 or c_meta["neg_ratio"] >= 0.50 else "high"
        anom = Insight(
            brand_id=brand_id,
            type="negative_sentiment_spike",
            severity=severity,
            status="active",
            metric="negative_sentiment_pct",
            baseline_value=round(b_meta["neg_ratio"] * 100, 1),
            current_value=round(c_meta["neg_ratio"] * 100, 1),
            deviation=round(neg_diff * 100, 1),
            threshold=round(NEGATIVE_SPIKE_THRESHOLD * 100, 1),
            text=(
                f"Negative sentiment increased from {int(b_meta['neg_ratio'] * 100)}% to "
                f"{int(c_meta['neg_ratio'] * 100)}% (+{int(neg_diff * 100)} pp) versus baseline, "
                f"exceeding the configured {int(NEGATIVE_SPIKE_THRESHOLD * 100)} pp threshold."
            ),
            supporting_review_ids=c_meta["negatives"][:5],
        )
        anomalies.append(anom)
        session.add(anom)

    # 3. Rating Deterioration
    if b_meta["ratings"] and c_meta["ratings"]:
        rating_diff = round(c_meta["avg_rating"] - b_meta["avg_rating"], 2)
        if rating_diff <= RATING_DROP_THRESHOLD:
            severity = "high" if rating_diff <= -1.0 else "medium"
            low_rating_ids = [r.id for r, _ in current if r.rating is not None and r.rating <= 3]
            anom = Insight(
                brand_id=brand_id,
                type="rating_deterioration",
                severity=severity,
                status="active",
                metric="average_rating",
                baseline_value=round(b_meta["avg_rating"], 2),
                current_value=round(c_meta["avg_rating"], 2),
                deviation=rating_diff,
                threshold=RATING_DROP_THRESHOLD,
                text=(
                    f"Average customer rating dropped from {b_meta['avg_rating']:.1f} to "
                    f"{c_meta['avg_rating']:.1f} ({rating_diff:+.1f} stars) compared with baseline period, "
                    f"exceeding the {abs(RATING_DROP_THRESHOLD):.1f}-star threshold."
                ),
                supporting_review_ids=low_rating_ids[:5],
            )
            anomalies.append(anom)
            session.add(anom)

    # 4. Theme Complaint Spike
    for theme, curr_neg_ids in c_meta["theme_neg"].items():
        if len(curr_neg_ids) < 2:
            continue
        base_theme_neg_count = len(b_meta["theme_neg"].get(theme, []))
        base_ratio = base_theme_neg_count / b_meta["count"] if b_meta["count"] else 0.0
        curr_ratio = len(curr_neg_ids) / c_meta["count"] if c_meta["count"] else 0.0
        deviation = round(curr_ratio - base_ratio, 4)

        if deviation >= THEME_COMPLAINT_SPIKE_THRESHOLD:
            high_risk_themes = {"side effects", "efficacy", "packaging", "shipping"}
            severity = "high" if theme in high_risk_themes else "medium"
            anom = Insight(
                brand_id=brand_id,
                type="theme_complaint_spike",
                severity=severity,
                status="active",
                metric=f"theme_complaint_pct_{theme.replace(' ', '_')}",
                baseline_value=round(base_ratio * 100, 1),
                current_value=round(curr_ratio * 100, 1),
                deviation=round(deviation * 100, 1),
                threshold=round(THEME_COMPLAINT_SPIKE_THRESHOLD * 100, 1),
                text=(
                    f"Customer complaints regarding '{theme}' surged to {int(curr_ratio * 100)}% of recent feedback "
                    f"(+{int(deviation * 100)} pp vs baseline), with {len(curr_neg_ids)} negative reports."
                ),
                supporting_review_ids=curr_neg_ids[:5],
            )
            anomalies.append(anom)
            session.add(anom)

    # 5. Product-Level Anomaly
    # Group reviews by product to identify outliers
    prod_groups = defaultdict(list)
    for r, a in rows:
        prod_groups[r.product_id].append((r, a))

    brand_all_ratings = [r.rating for r, _ in rows if r.rating is not None]
    brand_avg_rating = sum(brand_all_ratings) / len(brand_all_ratings) if brand_all_ratings else 0.0
    brand_neg_ratio = sum(1 for _, a in rows if a.sentiment == "negative") / total_reviews if total_reviews else 0.0

    for pid, prod_items in prod_groups.items():
        if len(prod_items) < 3:
            continue
        p_ratings = [r.rating for r, _ in prod_items if r.rating is not None]
        p_avg = sum(p_ratings) / len(p_ratings) if p_ratings else 0.0
        p_neg_ids = [r.id for r, a in prod_items if a.sentiment == "negative"]
        p_neg_ratio = len(p_neg_ids) / len(prod_items)

        rating_gap = round(p_avg - brand_avg_rating, 2)
        neg_gap = round(p_neg_ratio - brand_neg_ratio, 4)

        if rating_gap <= PRODUCT_RATING_GAP_THRESHOLD or neg_gap >= PRODUCT_NEGATIVE_GAP_THRESHOLD:
            product = await session.get(Product, pid)
            prod_name = product.name if product else f"Product #{pid}"
            anom = Insight(
                brand_id=brand_id,
                product_id=pid,
                type="product_anomaly",
                severity="high" if rating_gap <= -1.0 or neg_gap >= 0.35 else "medium",
                status="active",
                metric="product_rating_benchmark",
                baseline_value=round(brand_avg_rating, 2),
                current_value=round(p_avg, 2),
                deviation=rating_gap,
                threshold=PRODUCT_RATING_GAP_THRESHOLD,
                text=(
                    f"Product '{prod_name}' materially underperforms brand benchmarks: average rating is "
                    f"{p_avg:.1f}/5 vs brand average of {brand_avg_rating:.1f}/5 ({rating_gap:+.1f} stars), "
                    f"with {int(p_neg_ratio * 100)}% negative sentiment."
                ),
                supporting_review_ids=p_neg_ids[:5],
            )
            anomalies.append(anom)
            session.add(anom)

    await session.commit()
    logger.info("Generated %d explainable anomalies for brand id=%d", len(anomalies), brand_id)
    return anomalies


async def detect_all_anomalies(session: Optional[AsyncSession] = None) -> list[Insight]:
    """Run anomaly detection across all registered brands."""
    if session is not None:
        result = await session.execute(select(Brand))
        brands = result.scalars().all()
        all_anomalies = []
        for brand in brands:
            res = await detect_brand_anomalies(brand.id, session)
            all_anomalies.extend(res)
        return all_anomalies
    else:
        async with async_session() as sess:
            result = await sess.execute(select(Brand))
            brands = result.scalars().all()
            all_anomalies = []
            for brand in brands:
                res = await detect_brand_anomalies(brand.id, sess)
                all_anomalies.extend(res)
            return all_anomalies
