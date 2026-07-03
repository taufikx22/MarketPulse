import asyncio
import json
from datetime import datetime, date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import ARRAY
from sqlalchemy import select, func, event
import sqlite3

from app.database import Base
from app.models import Brand, Product, Review, ReviewAnalysis, Insight
from app.schemas import BrandOut, ProductOut, ReviewOut
from app.pipeline.sentiment import classify_sentiment
from app.pipeline.themes import tag_themes

# Compile rule for ARRAY type in SQLite
@compiles(ARRAY, 'sqlite')
def compile_array_sqlite(type_, compiler, **kw):
    return "TEXT"

# Emulate date_trunc in SQLite
def sqlite_date_trunc(trunc_type, date_str):
    if not date_str:
        return None
    try:
        # date_str is usually YYYY-MM-DD
        dt = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
        # Find start of week (Monday)
        monday = dt - datetime.timedelta(days=dt.weekday())
        return monday.strftime("%Y-%m-%d")
    except Exception:
        return date_str

async def run_tests():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    @event.listens_for(engine.sync_engine, "connect")
    def register_sqlite_funcs(dbapi_connection, connection_record):
        dbapi_connection.create_function("date_trunc", 2, sqlite_date_trunc)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Seed test data
        brand = Brand(name="Test Brand", url="https://test.com", category="longevity")
        session.add(brand)
        await session.flush()

        product = Product(brand_id=brand.id, name="Test Product", url="https://test.com/prod", price=100.0)
        session.add(product)
        await session.flush()

        # Add 3 reviews
        r1 = Review(product_id=product.id, raw_text="amazing energy booster", rating=5, text_hash="hash1", review_date=date(2026, 1, 10))
        r2 = Review(product_id=product.id, raw_text="tastes bad, average results", rating=3, text_hash="hash2", review_date=date(2026, 1, 12))
        r3 = Review(product_id=product.id, raw_text="completely useless package", rating=1, text_hash="hash3", review_date=date(2026, 1, 15))
        session.add_all([r1, r2, r3])
        await session.flush()

        # Add analysis records
        a1 = ReviewAnalysis(review_id=r1.id, sentiment="positive", sentiment_score=0.9, themes=json.dumps(["efficacy"]))
        a2 = ReviewAnalysis(review_id=r2.id, sentiment="neutral", sentiment_score=0.5, themes=json.dumps(["taste/flavor"]))
        a3 = ReviewAnalysis(review_id=r3.id, sentiment="negative", sentiment_score=0.1, themes=json.dumps(["packaging"]))
        session.add_all([a1, a2, a3])
        await session.commit()

        print("[OK] Seeded SQLite test database successfully!")

        # Query and verify
        # 1. Brands list
        res = await session.execute(select(Brand))
        brands = res.scalars().all()
        assert len(brands) == 1
        assert brands[0].name == "Test Brand"
        print("[OK] Brand query verification passed!")

        # 2. Sentiment trend query
        # Since we registered date_trunc, we can test the trend query:
        trend_query = select(
            func.date_trunc("week", Review.review_date).label("week"),
            ReviewAnalysis.sentiment,
            func.count().label("count"),
            func.avg(ReviewAnalysis.sentiment_score).label("avg_score")
        ).join(Product, Product.id == Review.product_id)\
         .join(ReviewAnalysis, ReviewAnalysis.review_id == Review.id)\
         .where(Product.brand_id == brand.id)\
         .group_by("week", ReviewAnalysis.sentiment)
        
        res = await session.execute(trend_query)
        rows = res.all()
        assert len(rows) > 0
        print("[OK] Sentiment trend query verification passed!")

if __name__ == "__main__":
    asyncio.run(run_tests())
