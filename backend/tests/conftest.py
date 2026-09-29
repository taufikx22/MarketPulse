import json
import pytest
import pytest_asyncio
from datetime import date, datetime, timedelta
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy import event

from app.database import Base, get_db
from app.main import app
from app.models.brand import Brand
from app.models.product import Product
from app.models.review import Review
from app.models.analysis import ReviewAnalysis
from app.models.insight import Insight


def sqlite_date_trunc(trunc_type, date_str):
    if not date_str:
        return None
    try:
        dt = datetime.strptime(str(date_str).split()[0], "%Y-%m-%d")
        monday = dt - timedelta(days=dt.weekday())
        return monday.strftime("%Y-%m-%d")
    except Exception:
        return str(date_str)


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create isolated in-memory SQLite database with StaticPool."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def register_sqlite_funcs(dbapi_connection, connection_record):
        dbapi_connection.create_function("date_trunc", 2, sqlite_date_trunc)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """Provide an isolated database session."""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def seeded_session(db_session):
    """Seed test data for brands, products, reviews, analyses, and insights."""
    # Brands
    b1 = Brand(name="Aura Longevity", url="https://auralongevity.test", category="longevity")
    b2 = Brand(name="Zenith Botanicals", url="https://zenithbotanicals.test", category="ayurveda")
    db_session.add_all([b1, b2])
    await db_session.flush()

    # Products
    p1 = Product(
        brand_id=b1.id,
        name="NMN 500mg Cell Booster",
        url="https://auralongevity.test/nmn",
        price=1499.0,
        description="High purity NMN",
    )
    p2 = Product(
        brand_id=b2.id,
        name="Ashwagandha Gold",
        url="https://zenithbotanicals.test/ashwa",
        price=899.0,
        description="Stress relief herbal supplement",
    )
    db_session.add_all([p1, p2])
    await db_session.flush()

    # Reviews
    r1 = Review(
        product_id=p1.id,
        author="Alice",
        rating=5,
        review_date=date(2026, 1, 10),
        raw_text="Incredible energy boost and vitality after 2 weeks of use!",
        text_hash="hash_alice_1",
    )
    r2 = Review(
        product_id=p1.id,
        author="Bob",
        rating=4,
        review_date=date(2026, 1, 12),
        raw_text="Noticeable focus improvements, but slightly expensive.",
        text_hash="hash_bob_2",
    )
    r3 = Review(
        product_id=p1.id,
        author="Charlie",
        rating=1,
        review_date=date(2026, 1, 15),
        raw_text="Terrible delivery and damaged packaging on arrival.",
        text_hash="hash_charlie_3",
    )
    r4 = Review(
        product_id=p2.id,
        author="Dana",
        rating=5,
        review_date=date(2026, 1, 20),
        raw_text="Deep restful sleep, best herbal supplement I have tried.",
        text_hash="hash_dana_4",
    )
    db_session.add_all([r1, r2, r3, r4])
    await db_session.flush()

    # Analyses
    a1 = ReviewAnalysis(
        review_id=r1.id,
        sentiment="positive",
        sentiment_score=0.92,
        themes=json.dumps(["efficacy", "energy"]),
    )
    a2 = ReviewAnalysis(
        review_id=r2.id,
        sentiment="positive",
        sentiment_score=0.74,
        themes=json.dumps(["efficacy", "price/value"]),
    )
    a3 = ReviewAnalysis(
        review_id=r3.id,
        sentiment="negative",
        sentiment_score=0.15,
        themes=json.dumps(["packaging", "shipping"]),
    )
    a4 = ReviewAnalysis(
        review_id=r4.id,
        sentiment="positive",
        sentiment_score=0.88,
        themes=json.dumps(["sleep", "efficacy"]),
    )
    db_session.add_all([a1, a2, a3, a4])
    await db_session.flush()

    # Insights
    ins1 = Insight(
        brand_id=b1.id,
        type="strength",
        text="Customers consistently praise high efficacy and energy benefits.",
        supporting_review_ids=json.dumps([r1.id, r2.id]),
        generated_at=datetime.utcnow(),
    )
    ins2 = Insight(
        brand_id=b1.id,
        type="churn_risk",
        text="Damaged packaging and shipping delays cause negative feedback.",
        supporting_review_ids=json.dumps([r3.id]),
        generated_at=datetime.utcnow(),
    )
    db_session.add_all([ins1, ins2])
    await db_session.commit()

    return {
        "brands": [b1, b2],
        "products": [p1, p2],
        "reviews": [r1, r2, r3, r4],
        "insights": [ins1, ins2],
    }


@pytest_asyncio.fixture(scope="function")
async def client(db_engine, seeded_session):
    """Async HTTP test client with isolated SQLite database dependency override."""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
