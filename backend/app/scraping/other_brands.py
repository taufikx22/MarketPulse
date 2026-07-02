import json
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from app.scraping.base import BrandScraper


class KapivaScraper(BrandScraper):
    brand_name = "Kapiva"
    base_url = "https://kapiva.in"
    rate_limit = 3.0

    async def scrape_products(self) -> list[dict]:
        products = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                resp = await page.goto(f"{self.base_url}/products.json?limit=50", wait_until="networkidle", timeout=15000)
                if resp and resp.ok:
                    raw = await page.inner_text("body")
                    self.save_raw(raw, "products_raw.json")
                    data = json.loads(raw)
                    for item in data.get("products", []):
                        price = None
                        if item.get("variants"):
                            price_str = item["variants"][0].get("price")
                            if price_str:
                                price = float(price_str)
                        image_url = item["images"][0]["src"] if item.get("images") else None
                        products.append({
                            "name": item.get("title", ""),
                            "url": f"{self.base_url}/products/{item.get('handle', '')}",
                            "price": price,
                            "description": _strip_html(item.get("body_html", "")),
                            "image_url": image_url,
                        })
            except Exception:
                pass
            await browser.close()
        return products

    async def scrape_reviews(self, product_url: str, product_name: str) -> list[dict]:
        reviews = []
        slug = product_url.rstrip("/").split("/")[-1]
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(product_url, wait_until="networkidle", timeout=20000)
                self._delay()
                await page.wait_for_timeout(3000)
                html = await page.content()
                self.save_raw(html, f"reviews_{slug}.html")
                reviews = _parse_shopify_reviews(html)
            except Exception as e:
                self.save_raw({"error": str(e)}, f"reviews_{slug}_error.json")
            finally:
                await browser.close()
        return reviews


class OzivaScraper(BrandScraper):
    brand_name = "OZiva"
    base_url = "https://oziva.in"
    rate_limit = 3.0

    async def scrape_products(self) -> list[dict]:
        products = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                resp = await page.goto(f"{self.base_url}/products.json?limit=50", wait_until="networkidle", timeout=15000)
                if resp and resp.ok:
                    raw = await page.inner_text("body")
                    self.save_raw(raw, "products_raw.json")
                    data = json.loads(raw)
                    for item in data.get("products", []):
                        price = None
                        if item.get("variants"):
                            price_str = item["variants"][0].get("price")
                            if price_str:
                                price = float(price_str)
                        image_url = item["images"][0]["src"] if item.get("images") else None
                        products.append({
                            "name": item.get("title", ""),
                            "url": f"{self.base_url}/products/{item.get('handle', '')}",
                            "price": price,
                            "description": _strip_html(item.get("body_html", "")),
                            "image_url": image_url,
                        })
            except Exception:
                pass
            await browser.close()
        return products

    async def scrape_reviews(self, product_url: str, product_name: str) -> list[dict]:
        reviews = []
        slug = product_url.rstrip("/").split("/")[-1]
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(product_url, wait_until="networkidle", timeout=20000)
                self._delay()
                await page.wait_for_timeout(3000)
                html = await page.content()
                self.save_raw(html, f"reviews_{slug}.html")
                reviews = _parse_shopify_reviews(html)
            except Exception as e:
                self.save_raw({"error": str(e)}, f"reviews_{slug}_error.json")
            finally:
                await browser.close()
        return reviews


def _strip_html(html_str: str) -> str:
    if not html_str:
        return ""
    return BeautifulSoup(html_str, "lxml").get_text(separator=" ", strip=True)


def _parse_shopify_reviews(html: str) -> list[dict]:
    """Shared parser for Shopify review widgets (Judge.me, Yotpo, SPR)."""
    soup = BeautifulSoup(html, "lxml")
    reviews = []

    # Judge.me
    for rev in soup.select(".jdgm-rev"):
        body = rev.select_one(".jdgm-rev__body")
        if not body:
            continue
        author_el = rev.select_one(".jdgm-rev__author")
        date_el = rev.select_one(".jdgm-rev__timestamp")
        rating_el = rev.select_one("[data-score]")
        rating = None
        if rating_el and rating_el.get("data-score"):
            try:
                rating = int(float(rating_el["data-score"]))
            except ValueError:
                pass
        reviews.append({
            "text": body.get_text(strip=True),
            "author": author_el.get_text(strip=True) if author_el else None,
            "date": date_el.get_text(strip=True) if date_el else None,
            "rating": rating,
        })

    if reviews:
        return reviews

    # Yotpo
    for rev in soup.select(".yotpo-review"):
        body = rev.select_one(".content-review, .yotpo-review-content")
        if not body:
            continue
        author_el = rev.select_one(".yotpo-user-name")
        date_el = rev.select_one(".yotpo-review-date")
        stars = rev.select(".yotpo-icon-star")
        reviews.append({
            "text": body.get_text(strip=True),
            "author": author_el.get_text(strip=True) if author_el else None,
            "date": date_el.get_text(strip=True) if date_el else None,
            "rating": len(stars) if stars else None,
        })

    if reviews:
        return reviews

    # Generic SPR
    for rev in soup.select(".spr-review, .review, [data-review]"):
        body = rev.select_one(".spr-review-content-body, .review-body, .review-text")
        if not body:
            continue
        author_el = rev.select_one(".spr-review-header-byline, .review-author")
        reviews.append({
            "text": body.get_text(strip=True),
            "author": author_el.get_text(strip=True) if author_el else None,
            "date": None,
            "rating": None,
        })

    return reviews
