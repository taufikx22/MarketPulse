import io
import pytest


@pytest.mark.asyncio
async def test_import_empty_file_fails(client):
    response = await client.post(
        "/brands/import",
        data={"brand_name": "Test Import Brand"},
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_import_empty_brand_name_fails(client):
    csv_content = b"product_name,review_text,rating\nProd A,Great stuff,5\n"
    response = await client.post(
        "/brands/import",
        data={"brand_name": "   "},
        files={"file": ("reviews.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 400
    assert "Brand name is required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_import_valid_csv_success(client):
    csv_content = (
        b"product_name,review_text,rating,author,date\n"
        b"Super Greens,Fantastic everyday health boost!,5,Sam,2026-02-01\n"
        b"Super Greens,Tastes a bit earthy but works well.,4,Taylor,2026-02-03\n"
    )
    response = await client.post(
        "/brands/import",
        data={"brand_name": "Greens Co"},
        files={"file": ("greens.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["brand"]["name"] == "Greens Co"
    assert data["summary"]["products_imported_or_updated"] == 1
    assert data["summary"]["new_reviews_inserted"] == 2


@pytest.mark.asyncio
async def test_import_valid_json_success(client):
    json_content = (
        b'[\n'
        b'  {"name": "Omega 3 Ultra", "url": "https://test.com/omega", "reviews": ['
        b'    {"text": "Very clean fish oil with zero fishy burps.", "rating": 5},'
        b'    {"text": "Good pills, easy to swallow without aftertaste.", "rating": 4}'
        b'  ]}\n'
        b']'
    )
    response = await client.post(
        "/brands/import",
        data={"brand_name": "Pure Ocean"},
        files={"file": ("reviews.json", json_content, "application/json")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["brand"]["name"] == "Pure Ocean"
    assert data["summary"]["products_imported_or_updated"] == 1
    assert data["summary"]["new_reviews_inserted"] == 2


@pytest.mark.asyncio
async def test_import_malformed_json_fails(client):
    json_content = b'{"not_a_valid_list": true'
    response = await client.post(
        "/brands/import",
        data={"brand_name": "Broken Brand"},
        files={"file": ("broken.json", json_content, "application/json")},
    )
    assert response.status_code == 400
    assert "Failed to parse JSON file" in response.json()["detail"]
