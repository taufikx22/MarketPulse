from sqlalchemy import String, DateTime, ForeignKey, Text, ARRAY, Integer, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from app.database import Base


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(50))
    text: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    supporting_review_ids: Mapped[Optional[list[int]]] = mapped_column(ARRAY(Integer), nullable=True)

    # Control / Anomaly Engine fields
    severity: Mapped[Optional[str]] = mapped_column(String(20), default="medium", nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(20), default="active", nullable=True)
    metric: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    baseline_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deviation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)

    brand = relationship("Brand", back_populates="insights")
    product = relationship("Product", foreign_keys=[product_id])
