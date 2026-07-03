import csv
import io
import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.brand import Brand
from app.models.product import Product
from app.models.review import Review
from app.pipeline.cleaning import clean_product, clean_review
from app.pipeline.enrich import enrich_reviews
from app.pipeline.insights import generate_brand_insights
from app.scraping.run_scrape import run_scrape, SCRAPERS

router = APIRouter(tags=["ingestion"])


@router.post("/brands/import")
async def import_brand_data(
    file: UploadFile = File(...),
    brand_name: str = Form(...),
    brand_url: Optional[str] = Form(None),
    category: Optional[str] = Form("wellness"),
    db: AsyncSession = Depends(get_db),
):
    """Import brand data (products and reviews) from uploaded JSON/CSV files."""
    contents = await file.read()
    filename = file.filename.lower() if file.filename else ""

    products_data = []

    if filename.endswith(".json"):
        try:
            raw_data = json.loads(contents.decode("utf-8"))
            # Standard structural format: { "products": [ { "name", "url", "price", ..., "reviews": [...] } ] }
            if isinstance(raw_data, dict):
                # Optionally override brand metadata if present in JSON
                brand_name = raw_data.get("brand_name", brand_name)
                brand_url = raw_data.get("brand_url") or raw_data.get("base_url") or brand_url
                category = raw_data.get("category", category)
                products_list = raw_data.get("products", [])
            elif isinstance(raw_data, list):
                products_list = raw_data
            else:
                raise HTTPException(400, "JSON must be an object or a list")

            for p_raw in products_list:
                products_data.append({
                    "name": p_raw.get("name", "").strip(),
                    "url": p_raw.get("url", "").strip(),
                    "price": p_raw.get("price"),
                    "description": p_raw.get("description", ""),
                    "image_url": p_raw.get("image_url"),
                    "reviews": p_raw.get("reviews", [])
                })
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(400, f"Failed to parse JSON file: {e}")

    elif filename.endswith(".csv"):
        try:
            text_data = contents.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text_data))

            # Helper to map columns flexibly
            def find_col(row, *aliases):
                for alias in aliases:
                    for key in row.keys():
                        if key.lower().strip() == alias.lower():
                            return row[key]
                return None

            # Group reviews by product in memory
            prod_map = {}
            for row in reader:
                p_name = find_col(row, "product_name", "product", "name") or "Generic Product"
                p_url = find_col(row, "product_url", "url") or f"https://imported.com/{p_name.replace(' ', '-').lower()}"
                p_price = find_col(row, "price", "product_price")
                p_desc = find_col(row, "description", "desc") or ""
                p_img = find_col(row, "image_url", "image")

                rev_text = find_col(row, "review_text", "text", "review", "content")
                rev_rating = find_col(row, "rating", "score", "stars")
                rev_author = find_col(row, "author", "reviewer", "name")
                rev_date = find_col(row, "review_date", "date")

                if p_url not in prod_map:
                    prod_map[p_url] = {
                        "name": p_name,
                        "url": p_url,
                        "price": p_price,
                        "description": p_desc,
                        "image_url": p_img,
                        "reviews": []
                    }

                if rev_text:
                    prod_map[p_url]["reviews"].append({
                        "text": rev_text,
                        "rating": int(rev_rating) if rev_rating and str(rev_rating).isdigit() else None,
                        "author": rev_author,
                        "date": rev_date
                    })
            
            products_data = list(prod_map.values())
        except Exception as e:
            raise HTTPException(400, f"Failed to parse CSV file: {e}")
    else:
        raise HTTPException(400, "Unsupported file format. Please upload JSON or CSV.")

    if not products_data:
        raise HTTPException(400, "No products or reviews found in the uploaded file.")

    # 1. Resolve or create the Brand
    res = await db.execute(select(Brand).where(Brand.name == brand_name))
    brand = res.scalar_one_or_none()
    if not brand:
        brand = Brand(
            name=brand_name,
            url=brand_url or f"https://{brand_name.replace(' ', '').lower()}.com",
            category=category or "wellness",
        )
        db.add(brand)
        await db.flush()

    total_products = 0
    total_reviews = 0
    total_dupes = 0

    # 2. Add products and reviews
    for p_raw in products_data:
        cleaned_p = clean_product(p_raw)
        if not cleaned_p["name"]:
            continue

        # Find/update/create product
        res = await db.execute(select(Product).where(Product.url == cleaned_p["url"]))
        product = res.scalar_one_or_none()
        if product:
            product.name = cleaned_p["name"]
            product.price = cleaned_p["price"]
            product.description = cleaned_p["description"]
            if cleaned_p["image_url"]:
                product.image_url = cleaned_p["image_url"]
            product.last_scraped_at = datetime.now(timezone.utc)
        else:
            product = Product(
                brand_id=brand.id,
                last_scraped_at=datetime.now(timezone.utc),
                **cleaned_p
            )
            db.add(product)
            total_products += 1
        await db.flush()

        # Add reviews
        for r_raw in p_raw.get("reviews", []):
            cleaned_r = clean_review(r_raw, product.id)
            if not cleaned_r:
                continue

            # Check for duplicate
            dup = await db.execute(select(Review).where(Review.text_hash == cleaned_r["text_hash"]))
            if dup.scalar_one_or_none():
                total_dupes += 1
                continue

            review = Review(**cleaned_r)
            db.add(review)
            total_reviews += 1

    await db.commit()

    # 3. Trigger NLP enrichment to compute sentiment, themes, and embeddings immediately
    if total_reviews > 0:
        await enrich_reviews()
        await generate_brand_insights(brand.id, db)

    return {
        "status": "success",
        "brand": {
            "id": brand.id,
            "name": brand.name,
            "category": brand.category
        },
        "summary": {
            "products_imported_or_updated": len(products_data),
            "new_products_created": total_products,
            "new_reviews_inserted": total_reviews,
            "duplicate_reviews_skipped": total_dupes
        }
    }


@router.post("/brands/{brand_id}/scrape")
async def trigger_brand_scrape(
    brand_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger background scraping of reviews and products for a supported brand."""
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")

    # Match brand name to scraper keys
    brand_key = None
    name_lower = brand.name.lower()
    for key in SCRAPERS.keys():
        if key.replace("_", "") in name_lower or name_lower in key:
            brand_key = key
            break

    if not brand_key:
        # Fallback to key matches in name
        if "decode" in name_lower:
            brand_key = "decode_age"
        elif "kapiva" in name_lower:
            brand_key = "kapiva"
        elif "oziva" in name_lower:
            brand_key = "oziva"
        else:
            raise HTTPException(
                400,
                f"No automatic scraper registered for brand '{brand.name}'. Supported scrapers: {list(SCRAPERS.keys())}. Please import data via JSON/CSV instead."
            )

    # Run scraping and enrichment asynchronously in the background
    async def scrape_and_enrich_task():
        await run_scrape(brand_key)
        await enrich_reviews()
        from app.database import async_session
        async with async_session() as session:
            await generate_brand_insights(brand_id, session)

    background_tasks.add_task(scrape_and_enrich_task)

    return {
        "status": "scraping_started",
        "brand_name": brand.name,
        "brand_key": brand_key,
        "detail": "Scrape task has been queued in the background. It will clean and enrich reviews automatically when finished."
    }


@router.post("/brands/scrape")
async def trigger_brand_scrape_by_key(
    brand_key: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger background scraping of reviews and products for a supported brand key, creating the brand if needed."""
    if brand_key not in SCRAPERS:
        raise HTTPException(
            400,
            f"Unsupported brand key '{brand_key}'. Supported keys: {list(SCRAPERS.keys())}"
        )

    scraper_cls = SCRAPERS[brand_key]
    scraper = scraper_cls()

    # Find or create brand by base URL
    res = await db.execute(select(Brand).where(Brand.url == scraper.base_url))
    brand = res.scalar_one_or_none()
    if not brand:
        brand = Brand(
            name=scraper.brand_name,
            url=scraper.base_url,
            category="wellness supplements" if brand_key == "decode_age" else "ayurvedic wellness" if brand_key == "kapiva" else "plant-based nutrition",
        )
        db.add(brand)
        await db.flush()
        await db.commit()
        # Refetch inside a session
        res = await db.execute(select(Brand).where(Brand.url == scraper.base_url))
        brand = res.scalar_one_or_none()

    async def scrape_and_enrich_task():
        await run_scrape(brand_key)
        await enrich_reviews()
        from app.database import async_session
        async with async_session() as session:
            # Resolve brand_id again
            res_b = await session.execute(select(Brand).where(Brand.url == scraper.base_url))
            b_val = res_b.scalar_one_or_none()
            if b_val:
                await generate_brand_insights(b_val.id, session)

    background_tasks.add_task(scrape_and_enrich_task)

    return {
        "status": "scraping_started",
        "brand_id": brand.id,
        "brand_name": brand.name,
        "brand_key": brand_key,
        "detail": f"Scrape task for {brand.name} has been queued in the background. It will clean and enrich reviews automatically when finished."
    }

