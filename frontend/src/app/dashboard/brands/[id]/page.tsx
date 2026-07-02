'use client';

import { useEffect, useState, use } from 'react';
import { api, Brand, Product, Review, SentimentTrend, ThemeData } from '@/lib/api';
import SentimentTrendChart from '@/components/charts/SentimentTrendChart';
import ThemeBreakdownChart from '@/components/charts/ThemeBreakdownChart';
import styles from './brand-detail.module.css';

export default function BrandDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const brandId = parseInt(id);

  const [brand, setBrand] = useState<Brand | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [trend, setTrend] = useState<SentimentTrend[]>([]);
  const [themes, setThemes] = useState<ThemeData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.brand(brandId),
      api.products(brandId),
      api.reviews(brandId, 100),
      api.sentimentTrend(brandId).catch(() => []),
      api.themes(brandId).catch(() => []),
    ]).then(([b, p, r, t, th]) => {
      setBrand(b);
      setProducts(p);
      setReviews(r);
      setTrend(t);
      setThemes(th);
      setLoading(false);
    });
  }, [brandId]);

  if (loading) {
    return (
      <div>
        <div className="skeleton" style={{ height: 28, width: 200, marginBottom: 24 }} />
        <div className="skeleton" style={{ height: 280, marginBottom: 24 }} />
        <div className="skeleton" style={{ height: 200 }} />
      </div>
    );
  }

  if (!brand) {
    return <div className="empty-state"><p>Brand not found</p></div>;
  }

  const sentimentBadge = (sentiment: string) => {
    const cls = sentiment === 'positive' ? 'badge--positive' : sentiment === 'negative' ? 'badge--negative' : 'badge--neutral';
    return <span className={`badge ${cls}`}>{sentiment}</span>;
  };

  return (
    <div>
      <div className={styles.header}>
        <div>
          <h1>{brand.name}</h1>
          <p className={styles.meta}>
            {brand.category} · {products.length} products · {reviews.length} reviews
          </p>
        </div>
        <a href={brand.url} target="_blank" rel="noopener noreferrer" className="btn btn--secondary">
          Visit site ↗
        </a>
      </div>

      <div className={styles.chartGrid}>
        <section className="card">
          <h2 className={styles.sectionTitle}>Sentiment Over Time</h2>
          <SentimentTrendChart data={trend} />
        </section>
        <section className="card">
          <h2 className={styles.sectionTitle}>Theme Breakdown</h2>
          <ThemeBreakdownChart data={themes} />
        </section>
      </div>

      <section className={styles.productsSection}>
        <h2 className={styles.sectionTitle}>Products</h2>
        <div className={styles.productGrid}>
          {products.map(p => (
            <div key={p.id} className={`card ${styles.productCard}`}>
              <h3 className={styles.productName}>{p.name}</h3>
              {p.price && <span className={styles.price}>₹{p.price.toLocaleString()}</span>}
              {p.description && <p className={styles.productDesc}>{p.description.slice(0, 120)}{p.description.length > 120 ? '...' : ''}</p>}
            </div>
          ))}
        </div>
      </section>

      <section className={styles.reviewsSection}>
        <h2 className={styles.sectionTitle}>Recent Reviews</h2>
        <div className={styles.reviewList}>
          {reviews.slice(0, 20).map(r => (
            <div key={r.id} className={styles.reviewItem}>
              <div className={styles.reviewHeader}>
                <span className={styles.reviewAuthor}>{r.author || 'Anonymous'}</span>
                {r.rating && <span className={styles.rating}>{'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}</span>}
                {r.review_date && <span className={styles.reviewDate}>{r.review_date}</span>}
              </div>
              <p className={styles.reviewText}>{r.cleaned_text || r.raw_text}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
