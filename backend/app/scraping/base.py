import json
import os
import time
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from app.config import get_settings


class BrandScraper(ABC):
    """Base class for brand scrapers. Each subclass targets one website."""

    brand_name: str = ""
    base_url: str = ""
    # Seconds between requests — randomized around this value
    rate_limit: float = 2.0

    def __init__(self):
        self.staging_dir = Path(get_settings().staging_dir) / self._slug()
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def _slug(self) -> str:
        return self.brand_name.lower().replace(" ", "_")

    def _delay(self):
        jitter = random.uniform(0.5, 1.5)
        time.sleep(self.rate_limit * jitter)

    def save_raw(self, data: str | dict, filename: str):
        """Persist raw HTML or JSON to staging before parsing."""
        path = self.staging_dir / filename
        if isinstance(data, dict) or isinstance(data, list):
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            path.write_text(data, encoding="utf-8")
        return path

    def load_raw(self, filename: str) -> Optional[str]:
        path = self.staging_dir / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    @abstractmethod
    async def scrape_products(self) -> list[dict]:
        """Return a list of product dicts with keys: name, url, price, description, image_url"""
        ...

    @abstractmethod
    async def scrape_reviews(self, product_url: str, product_name: str) -> list[dict]:
        """Return a list of review dicts with keys: text, rating, author, date"""
        ...

    async def run(self) -> dict:
        """Full scrape: products → reviews for each product. Returns summary stats."""
        products = await self.scrape_products()
        total_reviews = 0
        for product in products:
            reviews = await self.scrape_reviews(product["url"], product["name"])
            product["reviews"] = reviews
            total_reviews += len(reviews)

        self.save_raw(products, f"full_scrape_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json")
        return {"brand": self.brand_name, "products": len(products), "reviews": total_reviews}
