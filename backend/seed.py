"""Seed the database with Decode Age as the first tracked brand, plus a handful of
manually curated products and realistic review data so the schema can be validated
before hooking up the scraper."""

import asyncio
import hashlib
from datetime import datetime, date, timezone
from sqlalchemy import text
from app.database import engine, async_session, Base
from app.models import Brand, Product, Review


DECODE_AGE_PRODUCTS = [
    {
        "name": "NMN Pro 500mg",
        "url": "https://decodeage.com/products/nmn-pro-500",
        "price": 3999.00,
        "description": "Uthever® NMN 500mg — pharmaceutical-grade nicotinamide mononucleotide for NAD+ restoration.",
        "image_url": "https://decodeage.com/cdn/shop/files/nmn-pro-500.webp",
    },
    {
        "name": "LongeVit",
        "url": "https://decodeage.com/products/longevit",
        "price": 2499.00,
        "description": "All-in-one longevity supplement with NMN, Trans-Resveratrol, Ca-AKG, TMG, and Spermidine.",
        "image_url": "https://decodeage.com/cdn/shop/files/longevit.webp",
    },
    {
        "name": "Trans-Resveratrol 500mg",
        "url": "https://decodeage.com/products/trans-resveratrol-500mg",
        "price": 1999.00,
        "description": "98%+ pure trans-resveratrol sourced from Japanese knotweed.",
        "image_url": "https://decodeage.com/cdn/shop/files/resveratrol.webp",
    },
    {
        "name": "Spermidine 5mg",
        "url": "https://decodeage.com/products/spermidine",
        "price": 2999.00,
        "description": "Wheat germ–derived spermidine to support cellular autophagy.",
        "image_url": "https://decodeage.com/cdn/shop/files/spermidine.webp",
    },
    {
        "name": "Ca-AKG 1000mg",
        "url": "https://decodeage.com/products/ca-akg",
        "price": 1799.00,
        "description": "Calcium Alpha-Ketoglutarate for biological age reduction and mitochondrial support.",
        "image_url": "https://decodeage.com/cdn/shop/files/ca-akg.webp",
    },
]

# Realistic-looking reviews — varied in tone, length, and specificity
SEED_REVIEWS = {
    "NMN Pro 500mg": [
        {"text": "Been taking this for about 6 weeks now. Definitely notice more sustained energy in the afternoons — I used to crash around 3pm and that's mostly gone. Pricey but I'll keep going for another couple months to see.", "rating": 4, "author": "Rajesh M.", "date": "2025-11-02"},
        {"text": "No noticeable difference after a month. Maybe I expected too much from the NAD+ hype. The capsules are easy to swallow at least.", "rating": 3, "author": "Sneha K.", "date": "2025-10-18"},
        {"text": "Third bottle in. My sleep tracker shows about 15 minutes more deep sleep per night compared to before, which I'll take. Delivery was fast — got it in 2 days to Bangalore.", "rating": 5, "author": "Arun P.", "date": "2025-12-05"},
        {"text": "Packaging was damaged when it arrived, one capsule was cracked open. The product itself seems fine based on other reviews but not a great first impression.", "rating": 2, "author": "Priyanka S.", "date": "2025-09-30"},
        {"text": "I take this with resveratrol from the same brand. Skin looks better, energy is up, and my last blood work showed improved markers. Worth the investment.", "rating": 5, "author": "Vikram T.", "date": "2026-01-14"},
    ],
    "LongeVit": [
        {"text": "Convenient to have everything in one capsule instead of buying 5 separate supplements. Price makes sense when you add up what you'd pay individually.", "rating": 5, "author": "Meera J.", "date": "2025-11-22"},
        {"text": "Gave me mild stomach discomfort the first few days. Went away after the first week. Energy boost is real though.", "rating": 4, "author": "Karthik R.", "date": "2025-12-10"},
        {"text": "Bought this for my father (65). He says he feels 'less tired' which is honestly a win. Will reorder.", "rating": 4, "author": "Divya N.", "date": "2025-10-05"},
        {"text": "The dosages of individual ingredients are lower than standalone products. If you're serious about longevity, probably better to buy each separately at higher doses.", "rating": 3, "author": "Nikhil G.", "date": "2026-02-18"},
    ],
    "Trans-Resveratrol 500mg": [
        {"text": "Great value compared to international brands. Lab tested, transparent about the source. Been using for 3 months alongside intermittent fasting.", "rating": 5, "author": "Siddharth V.", "date": "2025-11-15"},
        {"text": "The capsule size is perfect. I've tried resveratrol from another brand that was huge and hard to swallow. This one is much better.", "rating": 4, "author": "Ananya D.", "date": "2025-12-28"},
        {"text": "Shipping took 8 days to reach Kolkata which felt long. Product seems good quality though.", "rating": 3, "author": "Rohit B.", "date": "2026-01-05"},
    ],
    "Spermidine 5mg": [
        {"text": "Started taking this to support autophagy alongside my 16:8 fasting protocol. Too early to tell if it's making a measurable difference but I trust the research.", "rating": 4, "author": "Tanvi S.", "date": "2025-12-01"},
        {"text": "Very niche product, glad an Indian brand is making this available. Previously had to import from the US at 3x the price.", "rating": 5, "author": "Amit K.", "date": "2025-10-20"},
        {"text": "Not sure this does anything. Been taking for 2 months and I feel the same. Maybe the effects are subclinical.", "rating": 3, "author": "Pooja R.", "date": "2026-01-30"},
    ],
    "Ca-AKG 1000mg": [
        {"text": "Reasonably priced. I've read the mice studies on biological age reduction, trying it for myself. 1000mg dose is solid.", "rating": 4, "author": "Harsh L.", "date": "2025-11-08"},
        {"text": "Ordered two bottles during the sale. One bottle had the seal already broken — customer service replaced it quickly though, so I'll give them credit for that.", "rating": 3, "author": "Swati M.", "date": "2025-12-22"},
        {"text": "Pairs well with NMN if you're stacking. I do NMN in the morning and Ca-AKG in the evening. Energy and recovery have been noticeably better.", "rating": 5, "author": "Gaurav C.", "date": "2026-02-10"},
        {"text": "Mild digestive issues for the first 3 days. Fine after that. Taking it on an empty stomach seemed to cause the problem — now take with food.", "rating": 4, "author": "Nandini W.", "date": "2026-01-19"},
    ],
}


def make_hash(text: str, product_id: int) -> str:
    return hashlib.sha256(f"{text.strip().lower()}:{product_id}".encode()).hexdigest()


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        existing = await session.execute(text("SELECT count(*) FROM brands"))
        if existing.scalar() > 0:
            print("Database already has data — skipping seed.")
            return

        brand = Brand(
            name="Decode Age",
            url="https://decodeage.com",
            category="longevity supplements",
        )
        session.add(brand)
        await session.flush()

        for prod_data in DECODE_AGE_PRODUCTS:
            product = Product(
                brand_id=brand.id,
                last_scraped_at=datetime.now(timezone.utc),
                **prod_data,
            )
            session.add(product)
            await session.flush()

            for rev in SEED_REVIEWS.get(prod_data["name"], []):
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

        await session.commit()
        print(f"Seeded: {brand.name} with {len(DECODE_AGE_PRODUCTS)} products and {sum(len(v) for v in SEED_REVIEWS.values())} reviews.")


if __name__ == "__main__":
    asyncio.run(seed())
