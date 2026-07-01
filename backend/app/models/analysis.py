from sqlalchemy import String, ForeignKey, Float, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.database import Base


class ReviewAnalysis(Base):
    __tablename__ = "review_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), unique=True)
    sentiment: Mapped[str] = mapped_column(String(20))
    sentiment_score: Mapped[float] = mapped_column(Float)
    themes: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    review = relationship("Review", back_populates="analysis")
