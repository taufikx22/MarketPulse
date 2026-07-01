from sqlalchemy import String, DateTime, ForeignKey, SmallInteger, Text, Date, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from typing import Optional
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    raw_text: Mapped[str] = mapped_column(Text)
    cleaned_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    text_hash: Mapped[str] = mapped_column(String(64), unique=True)

    product = relationship("Product", back_populates="reviews")
    analysis = relationship("ReviewAnalysis", back_populates="review", uselist=False, lazy="selectin")
