from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import brands, webhooks, org


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: nothing heavy for now — DB pool created lazily
    yield
    # shutdown


settings = get_settings()

app = FastAPI(
    title="MarketPulse API",
    description="Marketing & customer intelligence for wellness brands",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(brands.router)
app.include_router(webhooks.router)
app.include_router(org.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
