import json
import re
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from app.scraping.base import BrandScraper


class DecodeAgeScraper(BrandScraper):
    brand_name = "Decode Age"
    base_url = "https://decodeage.com"
    rate_limit = 3.0  # be polite — they're a smaller brand

    async def scrape_products(self) -> list[dict]:
        """Scrape the product listing from Decode Age's collections page.
        Most Shopify sites expose product data as JSON at /products.json"""
        products = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Try the Shopify JSON endpoint first — much cleaner than parsing HTML
            try:
                response = await page.goto(f"{self.base_url}/products.json?limit=50", wait_until="networkidle", timeout=15000)
                if response and response.ok:
                    raw = await page.inner_text("body")
                    self.save_raw(raw, "products_raw.json")
                    data = json.loads(raw)

                    for item in data.get("products", []):
                        price = None
                        if item.get("variants"):
                            price_str = item["variants"][0].get("price")
                            if price_str:
                                price = float(price_str)

                        image_url = None
                        if item.get("images"):
                            image_url = item["images"][0].get("src")

                        products.append({
                            "name": item.get("title", ""),
                            "url": f"{self.base_url}/products/{item.get('handle', '')}",
                            "price": price,
                            "description": _strip_html(item.get("body_html", "")),
                            "image_url": image_url,
                            "shopify_id": item.get("id"),
                        })
            except Exception:
                # Fallback: scrape the collections page HTML
                await page.goto(f"{self.base_url}/collections/all", wait_until="networkidle", timeout=20000)
                html = await page.content()
                self.save_raw(html, "collections_raw.html")
                products = self._parse_collections_html(html)

            await browser.close()

        return products

    def _parse_collections_html(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        products = []
        for card in soup.select(".product-card, .grid__item, [data-product-card]"):
            link = card.select_one("a[href*='/products/']")
            title = card.select_one(".product-card__title, .product__title, h3")
            price_el = card.select_one(".price, .product-price, [data-product-price]")
            img = card.select_one("img")

            if not link:
                continue

            href = link.get("href", "")
            if not href.startswith("http"):
                href = f"{self.base_url}{href}"

            price = None
            if price_el:
                price_match = re.search(r"[\d,]+\.?\d*", price_el.get_text())
                if price_match:
                    price = float(price_match.group().replace(",", ""))

            products.append({
                "name": title.get_text(strip=True) if title else "",
                "url": href,
                "price": price,
                "description": "",
                "image_url": img.get("src", "") if img else None,
            })
        return products

    async def scrape_reviews(self, product_url: str, product_name: str) -> list[dict]:
        """Scrape reviews for a single product. Tries multiple review widget patterns
        common on Shopify stores (Judge.me, Yotpo, Stamped, native Shopify reviews)."""
        reviews = []
        slug = product_url.rstrip("/").split("/")[-1]

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(product_url, wait_until="networkidle", timeout=20000)
                self._delay()

                # Wait for review widgets to load (they're usually injected by JS)
                await page.wait_for_timeout(3000)
                html = await page.content()
                self.save_raw(html, f"reviews_{slug}.html")

                # Try Judge.me widget
                reviews = self._parse_judgeme_reviews(html)

                # If no Judge.me, try Yotpo
                if not reviews:
                    reviews = self._parse_yotpo_reviews(html)

                # If nothing from widgets, try generic review patterns
                if not reviews:
                    reviews = self._parse_generic_reviews(html)

                # Pagination: try loading more reviews if a "load more" or "next" button exists
                page_num = 1
                while page_num < 5:  # cap at 5 pages to avoid hammering the site
                    next_button = await page.query_selector(
                        ".jdgm-paginate__next:not(.jdgm-paginate__next--disabled), "
                        ".spr-summary-actions-newreview + .spr-pagination .next, "
                        "[data-reviews-next], .yotpo-nav .yotpo-page-next"
                    )
                    if not next_button:
                        break
                    await next_button.click()
                    await page.wait_for_timeout(2000)
                    self._delay()
                    new_html = await page.content()
                    new_reviews = (
                        self._parse_judgeme_reviews(new_html) or
                        self._parse_yotpo_reviews(new_html) or
                        self._parse_generic_reviews(new_html)
                    )
                    if not new_reviews or len(new_reviews) <= len(reviews):
                        break
                    reviews = new_reviews
                    page_num += 1

            except Exception as e:
                self.save_raw({"error": str(e), "product": product_name}, f"reviews_{slug}_error.json")
            finally:
                await browser.close()

        return reviews

    def _parse_judgeme_reviews(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        reviews = []
        for rev in soup.select(".jdgm-rev"):
            body = rev.select_one(".jdgm-rev__body")
            author_el = rev.select_one(".jdgm-rev__author")
            date_el = rev.select_one(".jdgm-rev__timestamp")
            rating_el = rev.select_one("[data-score]")

            if not body:
                continue

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
        return reviews

    def _parse_yotpo_reviews(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        reviews = []
        for rev in soup.select(".yotpo-review"):
            body = rev.select_one(".content-review, .yotpo-review-content")
            author_el = rev.select_one(".yotpo-user-name")
            date_el = rev.select_one(".yotpo-review-date")
            stars = rev.select(".yotpo-icon-star")

            if not body:
                continue

            reviews.append({
                "text": body.get_text(strip=True),
                "author": author_el.get_text(strip=True) if author_el else None,
                "date": date_el.get_text(strip=True) if date_el else None,
                "rating": len(stars) if stars else None,
            })
        return reviews

    def _parse_generic_reviews(self, html: str) -> list[dict]:
        """Fallback for stores using Shopify native reviews or unknown widgets."""
        soup = BeautifulSoup(html, "lxml")
        reviews = []
        for rev in soup.select(".spr-review, .review, [data-review]"):
            body = rev.select_one(".spr-review-content-body, .review-body, .review-text, .review__text")
            author_el = rev.select_one(".spr-review-header-byline, .review-author, .review__author")
            date_el = rev.select_one(".spr-review-header-byline time, .review-date, .review__date")

            if not body:
                continue

            # Try to extract star rating from class names or aria attributes
            rating = None
            star_el = rev.select_one("[class*='star'], [data-rating], .spr-icon")
            if star_el:
                rating_str = star_el.get("data-rating") or ""
                stars_match = re.search(r"(\d)", rating_str)
                if stars_match:
                    rating = int(stars_match.group(1))

            reviews.append({
                "text": body.get_text(strip=True),
                "author": author_el.get_text(strip=True) if author_el else None,
                "date": date_el.get("datetime", date_el.get_text(strip=True)) if date_el else None,
                "rating": rating,
            })
        return reviews


def _strip_html(html_str: str) -> str:
    if not html_str:
        return ""
    soup = BeautifulSoup(html_str, "lxml")
    return soup.get_text(separator=" ", strip=True)
