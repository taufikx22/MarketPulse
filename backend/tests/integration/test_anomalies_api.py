import pytest
from app.models.insight import Insight


@pytest.mark.asyncio
async def test_api_trigger_detect_anomalies(client, seeded_session):
    """Test POST /insights/detect-anomalies triggers rule evaluation."""
    brand_id = seeded_session["brands"][0].id
    response = await client.post(f"/insights/detect-anomalies?brand_id={brand_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "anomalies_detected" in data
    assert "anomalies" in data


@pytest.mark.asyncio
async def test_api_filter_insights_by_anomaly_flag(client, db_session, seeded_session):
    """Test GET /insights?is_anomaly=true returns only records with metric configured."""
    brand_id = seeded_session["brands"][0].id
    anomaly_record = Insight(
        brand_id=brand_id,
        type="negative_sentiment_spike",
        severity="high",
        status="active",
        metric="negative_sentiment_pct",
        baseline_value=10.0,
        current_value=45.0,
        deviation=35.0,
        threshold=15.0,
        text="Negative sentiment increased from 10% to 45% (+35 pp).",
    )
    db_session.add(anomaly_record)
    await db_session.commit()

    # Query with is_anomaly=true
    resp_anom = await client.get("/insights?is_anomaly=true")
    assert resp_anom.status_code == 200
    data_anom = resp_anom.json()
    assert len(data_anom) >= 1
    assert all(item["metric"] is not None for item in data_anom)

    # Query with severity=high
    resp_sev = await client.get("/insights?severity=high")
    assert resp_sev.status_code == 200
    data_sev = resp_sev.json()
    assert len(data_sev) >= 1
    assert all(item["severity"] == "high" for item in data_sev)


@pytest.mark.asyncio
async def test_api_reindex_endpoint(client, seeded_session):
    """Test POST /search/reindex triggers review indexing into ChromaDB."""
    response = await client.post("/search/reindex")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "reviews_indexed" in data
    assert data["reviews_indexed"] >= 1
