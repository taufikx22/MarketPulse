from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(512))
    category: Mapped[str] = mapped_column(String(100), default="wellness")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    products = relationship("Product", back_populates="brand", lazy="selectin")
    insights = relationship("Insight", back_populates="brand", lazy="selectin")
