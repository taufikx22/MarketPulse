"""End-to-end integration: run the scraper for a brand, clean the data, and insert into Postgres.
Usage:  python -m app.scraping.run_scrape decode_age
"""

import asyncio
import sys
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import async_session, engine, Base
from app.models.brand import Brand
from app.models.product import Product
from app.models.review import Review
from app.pipeline.cleaning import clean_product, clean_review
from app.scraping.decode_age import DecodeAgeScraper
from app.scraping.other_brands import KapivaScraper, OzivaScraper


SCRAPERS = {
    "decode_age": DecodeAgeScraper,
    "kapiva": KapivaScraper,
    "oziva": OzivaScraper,
}


async def run_scrape(brand_key: str):
    scraper_cls = SCRAPERS.get(brand_key)
    if not scraper_cls:
        print(f"Unknown brand: {brand_key}. Available: {list(SCRAPERS.keys())}")
        return

    scraper = scraper_cls()
    print(f"Starting scrape for {scraper.brand_name}...")

    # 1. Scrape products (and reviews per product)
    products_raw = await scraper.scrape_products()
    print(f"  Found {len(products_raw)} products")

    # Scrape reviews for each product
    for prod in products_raw:
        reviews = await scraper.scrape_reviews(prod["url"], prod["name"])
        prod["reviews"] = reviews
        print(f"  {prod['name']}: {len(reviews)} reviews")

    # 2. Clean and insert into DB
    async with async_session() as session:
        # Find or create the brand
        result = await session.execute(
            select(Brand).where(Brand.url == scraper.base_url)
        )
        brand = result.scalar_one_or_none()
        if not brand:
            brand = Brand(
                name=scraper.brand_name,
                url=scraper.base_url,
                category="wellness supplements",
            )
            session.add(brand)
            await session.flush()

        total_new_reviews = 0
        total_dupes = 0

        for prod_raw in products_raw:
            cleaned = clean_product(prod_raw)

            # Upsert product by URL
            existing = await session.execute(
                select(Product).where(Product.url == cleaned["url"])
            )
            product = existing.scalar_one_or_none()
            if product:
                product.price = cleaned["price"]
                product.description = cleaned["description"]
                product.image_url = cleaned["image_url"]
                product.last_scraped_at = datetime.now(timezone.utc)
            else:
                product = Product(
                    brand_id=brand.id,
                    last_scraped_at=datetime.now(timezone.utc),
                    **cleaned,
                )
                session.add(product)
            await session.flush()

            for rev_raw in prod_raw.get("reviews", []):
                cleaned_rev = clean_review(rev_raw, product.id)
                if cleaned_rev is None:
                    continue

                # Check for duplicate
                dup = await session.execute(
                    select(Review).where(Review.text_hash == cleaned_rev["text_hash"])
                )
                if dup.scalar_one_or_none():
                    total_dupes += 1
                    continue

                session.add(Review(**cleaned_rev))
                total_new_reviews += 1

        await session.commit()
        print(f"\nDone: {total_new_reviews} new reviews inserted, {total_dupes} duplicates skipped.")


if __name__ == "__main__":
    brand = sys.argv[1] if len(sys.argv) > 1 else "decode_age"
    asyncio.run(run_scrape(brand))
