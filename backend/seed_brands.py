"""Seed additional brands (Kapiva, OZiva) with realistic product and review data."""

import asyncio
import hashlib
from datetime import datetime, date, timezone
from sqlalchemy import text, select
from app.database import engine, async_session, Base
from app.models import Brand, Product, Review


def make_hash(text: str, product_id: int) -> str:
    return hashlib.sha256(f"{text.strip().lower()}:{product_id}".encode()).hexdigest()


BRANDS_DATA = {
    "Kapiva": {
        "url": "https://kapiva.in",
        "category": "ayurvedic wellness",
        "products": [
            {"name": "Kapiva Himalayan Shilajit Resin", "url": "https://kapiva.in/products/himalayan-shilajit-resin", "price": 1299.00, "description": "Pure Himalayan Shilajit resin with 60%+ fulvic acid content."},
            {"name": "Kapiva Dia Free Juice", "url": "https://kapiva.in/products/dia-free-juice", "price": 499.00, "description": "Ayurvedic juice blend for blood sugar management with Karela, Jamun, and Amla."},
            {"name": "Kapiva Wild Amla Juice", "url": "https://kapiva.in/products/wild-amla-juice", "price": 399.00, "description": "Cold-pressed amla juice from wild-harvested Indian gooseberries."},
            {"name": "Kapiva Gut Care Juice", "url": "https://kapiva.in/products/gut-care-juice", "price": 449.00, "description": "Aloe vera and fiber blend for digestive health and regularity."},
        ],
        "reviews": {
            "Kapiva Himalayan Shilajit Resin": [
                {"text": "Using it for a month now, definite improvement in stamina during workouts. The resin dissolves well in warm water. Taste is earthy but manageable.", "rating": 5, "author": "Manish G.", "date": "2025-11-20"},
                {"text": "Product seems authentic based on the fulvic acid test. Price is reasonable compared to imported brands. My only gripe is the tiny jar — lasts about 3 weeks.", "rating": 4, "author": "Deepak S.", "date": "2025-12-08"},
                {"text": "Didn't notice any difference after 3 weeks. Maybe I need to take it longer. Packaging was good though.", "rating": 3, "author": "Ravi K.", "date": "2026-01-15"},
                {"text": "Received a jar with the seal already tampered. Had to get it replaced through customer support — took 5 days but they did handle it.", "rating": 2, "author": "Anita B.", "date": "2025-10-30"},
                {"text": "Best shilajit I've tried in India. Been using for 4 months straight and my energy levels are consistently better. The lab test certificate they include is a nice touch.", "rating": 5, "author": "Suresh R.", "date": "2026-02-01"},
            ],
            "Kapiva Dia Free Juice": [
                {"text": "My father's fasting sugar dropped from 180 to 145 over 2 months. Obviously combined with diet changes, but this helped. Taste is bitter but that's expected.", "rating": 4, "author": "Priya M.", "date": "2025-11-05"},
                {"text": "Tastes absolutely terrible. I know it's medicine basically, but they could at least make it slightly palatable. Skipping days because I dread drinking it.", "rating": 2, "author": "Anil T.", "date": "2025-12-22"},
                {"text": "Consistent use for 6 weeks, HbA1c went from 7.2 to 6.8. My doctor was surprised. Will continue.", "rating": 5, "author": "Sunita D.", "date": "2026-01-10"},
            ],
            "Kapiva Wild Amla Juice": [
                {"text": "Good quality amla juice. Tastes fresh, not like the processed concentrate you get elsewhere. Skin and hair have improved noticeably.", "rating": 5, "author": "Kavita P.", "date": "2025-11-18"},
                {"text": "Bottle leaked during shipping — the entire package was sticky. Product itself was fine once I cleaned it up. Please fix your packaging.", "rating": 3, "author": "Rahul V.", "date": "2026-01-28"},
            ],
            "Kapiva Gut Care Juice": [
                {"text": "Genuinely helped with my bloating issues. Drinking 30ml before breakfast. Took about a week to notice the difference.", "rating": 4, "author": "Neha S.", "date": "2025-12-15"},
                {"text": "The consistency is thick and slightly slimy which put me off initially. Got used to it. Stomach feels calmer overall.", "rating": 4, "author": "Vivek C.", "date": "2026-02-05"},
                {"text": "Overpriced for what's basically aloe vera juice. You can get the same thing at a local store for 1/3 the price.", "rating": 2, "author": "Amit J.", "date": "2025-10-12"},
            ],
        },
    },
    "OZiva": {
        "url": "https://oziva.in",
        "category": "plant-based nutrition",
        "products": [
            {"name": "OZiva Plant Protein", "url": "https://oziva.in/products/plant-protein", "price": 1999.00, "description": "Pea + brown rice protein blend, 25g per serving, with added vitamins and minerals."},
            {"name": "OZiva Biotin Hair Vitamins", "url": "https://oziva.in/products/biotin-hair-vitamins", "price": 699.00, "description": "Plant-based biotin with bamboo shoot extract for hair growth and thickness."},
            {"name": "OZiva HerBalance for PCOS", "url": "https://oziva.in/products/herbalance-pcos", "price": 899.00, "description": "Ayurvedic blend with Chasteberry, Myo-Inositol for hormonal balance."},
            {"name": "OZiva Daily Greens & Herbs", "url": "https://oziva.in/products/daily-greens", "price": 599.00, "description": "21 superfoods powder with wheatgrass, spirulina, and ashwagandha."},
        ],
        "reviews": {
            "OZiva Plant Protein": [
                {"text": "Chocolate flavor is decent for a plant protein — not chalky like some others I've tried. Mixes well in a shaker. Using it post-workout for 2 months.", "rating": 4, "author": "Arjun M.", "date": "2025-11-25"},
                {"text": "The protein content is good but the sweetener (stevia) aftertaste is strong. Wish they had an unflavored option. Digestibility is great though — no bloating unlike whey.", "rating": 3, "author": "Sneha R.", "date": "2025-12-14"},
                {"text": "Been comparing this with another plant protein brand. OZiva mixes smoother and tastes better. Price is slightly higher but worth it for the vitamin additions.", "rating": 5, "author": "Kiran L.", "date": "2026-01-20"},
                {"text": "Got this on sale. Solid product. My only complaint is the scoop is buried deep inside and getting it out makes a mess.", "rating": 4, "author": "Pankaj W.", "date": "2025-10-08"},
            ],
            "OZiva Biotin Hair Vitamins": [
                {"text": "3 months in and my hair fall has reduced noticeably. My hairdresser actually commented on it. Takes patience but works.", "rating": 5, "author": "Megha K.", "date": "2025-12-30"},
                {"text": "Capsules are easy to take. Not sure if the biotin is doing anything or if it's just the seasonal change, but hair feels thicker. Will finish the 6-month course before judging.", "rating": 4, "author": "Ritika S.", "date": "2026-01-05"},
                {"text": "Caused breakouts on my chin and jawline — classic biotin side effect. Had to stop after 2 weeks. Would've been nice if this was mentioned on the product page.", "rating": 2, "author": "Shruti N.", "date": "2025-11-10"},
                {"text": "No results after 2 months. Maybe my hair loss is genetic and this can't help with that. Disappointed.", "rating": 2, "author": "Anjali D.", "date": "2026-02-12"},
            ],
            "OZiva HerBalance for PCOS": [
                {"text": "This actually helped regulate my cycle after 2 months. Combining with exercise and diet obviously, but the timing correlates with starting this. Doctor approved.", "rating": 5, "author": "Pooja T.", "date": "2025-11-30"},
                {"text": "Mild improvement in acne, periods still irregular. On month 3, will give it more time since PCOS is a long-term thing.", "rating": 3, "author": "Sana A.", "date": "2026-01-22"},
                {"text": "The capsule size is huge. Hard to swallow without gagging. Ingredient list looks good on paper but the delivery format needs work.", "rating": 3, "author": "Nisha G.", "date": "2025-12-05"},
            ],
            "OZiva Daily Greens & Herbs": [
                {"text": "Tastes like grass, obviously, but I mix it with orange juice and it's fine. Energy levels are better and I feel less sluggish in the mornings.", "rating": 4, "author": "Varun H.", "date": "2025-12-20"},
                {"text": "Bought this to supplement my diet since I barely eat vegetables. Convenience factor is great. Slight stomach discomfort the first 3 days.", "rating": 4, "author": "Tanya B.", "date": "2026-02-08"},
            ],
        },
    },
}


async def seed_additional():
    async with async_session() as session:
        for brand_name, data in BRANDS_DATA.items():
            existing = await session.execute(
                select(Brand).where(Brand.name == brand_name)
            )
            if existing.scalar_one_or_none():
                print(f"{brand_name} already exists, skipping.")
                continue

            brand = Brand(name=brand_name, url=data["url"], category=data["category"])
            session.add(brand)
            await session.flush()

            total_reviews = 0
            for prod_data in data["products"]:
                product = Product(
                    brand_id=brand.id,
                    name=prod_data["name"],
                    url=prod_data["url"],
                    price=prod_data["price"],
                    description=prod_data["description"],
                    last_scraped_at=datetime.now(timezone.utc),
                )
                session.add(product)
                await session.flush()

                for rev in data["reviews"].get(prod_data["name"], []):
                    review = Review(
                        product_id=product.id,
                        raw_text=rev["text"],
                        cleaned_text=rev["text"],
                        rating=rev["rating"],
                        author=rev["author"],
                        review_date=date.fromisoformat(rev["date"]),
                        text_hash=make_hash(rev["text"], product.id),
                    )
                    session.add(review)
                    total_reviews += 1

            await session.commit()
            print(f"Seeded: {brand_name} — {len(data['products'])} products, {total_reviews} reviews")


if __name__ == "__main__":
    asyncio.run(seed_additional())
