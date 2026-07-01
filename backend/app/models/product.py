from sqlalchemy import String, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(String(1024))
    price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    brand = relationship("Brand", back_populates="products")
    reviews = relationship("Review", back_populates="product", lazy="selectin")
