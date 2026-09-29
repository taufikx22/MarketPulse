from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional


class BrandOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    url: str
    category: str
    created_at: datetime


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    brand_id: int
    name: str
    url: str
    price: Optional[float]
    description: Optional[str]
    image_url: Optional[str]
    last_scraped_at: Optional[datetime]


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    raw_text: str
    cleaned_text: Optional[str]
    rating: Optional[int]
    author: Optional[str]
    review_date: Optional[date]
    scraped_at: datetime


class ReviewAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    review_id: int
    sentiment: str
    sentiment_score: float
    themes: Optional[list[str]]
    embedding_id: Optional[str]


class InsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    brand_id: int
    type: str
    text: str
    generated_at: datetime
    supporting_review_ids: Optional[list[int]] = []
    severity: Optional[str] = "medium"
    status: Optional[str] = "active"
    metric: Optional[str] = None
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    deviation: Optional[float] = None
    threshold: Optional[float] = None
    product_id: Optional[int] = None


class EnrichedInsightOut(InsightOut):
    supporting_reviews: Optional[list[ReviewOut]] = []


class WatchlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    org_id: int
    brand_id: int


class WatchlistAdd(BaseModel):
    brand_id: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    clerk_user_id: str
    email: str
    name: str
