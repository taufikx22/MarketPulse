import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_get_brands_list(client, seeded_session):
    response = await client.get("/brands")
    assert response.status_code == 200
    brands = response.json()
    assert len(brands) >= 2
    names = [b["name"] for b in brands]
    assert "Aura Longevity" in names
    assert "Zenith Botanicals" in names


@pytest.mark.asyncio
async def test_get_brand_by_id_success(client, seeded_session):
    brand_id = seeded_session["brands"][0].id
    response = await client.get(f"/brands/{brand_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == brand_id
    assert data["name"] == "Aura Longevity"


@pytest.mark.asyncio
async def test_get_brand_by_id_not_found(client):
    response = await client.get("/brands/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Brand not found"


@pytest.mark.asyncio
async def test_get_brand_products(client, seeded_session):
    brand_id = seeded_session["brands"][0].id
    response = await client.get(f"/brands/{brand_id}/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) >= 1
    assert products[0]["name"] == "NMN 500mg Cell Booster"


@pytest.mark.asyncio
async def test_get_brand_reviews(client, seeded_session):
    brand_id = seeded_session["brands"][0].id
    response = await client.get(f"/brands/{brand_id}/reviews")
    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 3


@pytest.mark.asyncio
async def test_get_brand_sentiment_trend(client, seeded_session):
    brand_id = seeded_session["brands"][0].id
    response = await client.get(f"/brands/{brand_id}/sentiment-trend")
    assert response.status_code == 200
    trend = response.json()
    assert isinstance(trend, list)
    assert len(trend) > 0
    first = trend[0]
    assert "week" in first
    assert "sentiment" in first
    assert "count" in first
    assert "avg_score" in first


@pytest.mark.asyncio
async def test_get_brand_themes(client, seeded_session):
    brand_id = seeded_session["brands"][0].id
    response = await client.get(f"/brands/{brand_id}/themes")
    assert response.status_code == 200
    themes = response.json()
    assert isinstance(themes, list)
    assert len(themes) > 0
    theme_names = [t["theme"] for t in themes]
    assert "efficacy" in theme_names


@pytest.mark.asyncio
async def test_compare_brands_success(client, seeded_session):
    b1_id = seeded_session["brands"][0].id
    b2_id = seeded_session["brands"][1].id
    response = await client.get(f"/compare?brand_ids={b1_id},{b2_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["brand_name"] in ("Aura Longevity", "Zenith Botanicals")
    assert "product_count" in data[0]
    assert "avg_rating" in data[0]
    assert "sentiment" in data[0]


@pytest.mark.asyncio
async def test_compare_brands_insufficient_ids(client, seeded_session):
    b1_id = seeded_session["brands"][0].id
    response = await client.get(f"/compare?brand_ids={b1_id}")
    assert response.status_code == 400
    assert "Need at least 2 brand IDs" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_insights(client, seeded_session):
    response = await client.get("/insights")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert "type" in data[0]
    assert "text" in data[0]
    assert "supporting_reviews" in data[0]


@pytest.mark.asyncio
async def test_list_insights_filter_type(client, seeded_session):
    response = await client.get("/insights?type=strength")
    assert response.status_code == 200
    data = response.json()
    assert all(item["type"] == "strength" for item in data)


@pytest.mark.asyncio
async def test_semantic_search(client, seeded_session):
    response = await client.get("/search?q=energy")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert data["query"] == "energy"
    assert "results" in data


@pytest.mark.asyncio
async def test_semantic_search_short_query_fails(client):
    response = await client.get("/search?q=a")
    assert response.status_code == 422  # validation error: min_length 2
