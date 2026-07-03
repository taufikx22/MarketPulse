'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, Brand, Review } from '@/lib/api';
import Sparkline from '@/components/charts/Sparkline';
import IngestPanel from '@/components/ui/IngestPanel';
import styles from './overview.module.css';

interface BrandCard {
  brand: Brand;
  productCount: number;
  reviewCount: number;
  avgRating: number;
  recentScores: number[];
}

export default function OverviewPage() {
  const [cards, setCards] = useState<BrandCard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const brands = await api.brands();
      const cardData: BrandCard[] = [];

      for (const brand of brands) {
        const [products, reviews] = await Promise.all([
          api.products(brand.id),
          api.reviews(brand.id, 100),
        ]);

        const ratings = reviews.filter(r => r.rating != null).map(r => r.rating!);
        const avgRating = ratings.length > 0 ? ratings.reduce((a, b) => a + b, 0) / ratings.length : 0;

        // Generate sparkline from last few ratings
        const recentRatings = ratings.slice(0, 10);
        cardData.push({
          brand,
          productCount: products.length,
          reviewCount: reviews.length,
          avgRating: Math.round(avgRating * 10) / 10,
          recentScores: recentRatings.length > 1 ? recentRatings : [3, 3],
        });
      }

      setCards(cardData);
    } catch (err) {
      console.error('Failed to load brands:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div>
        <h1 className={styles.pageTitle}>Overview</h1>
        <div className={styles.grid}>
          {[1, 2, 3].map(i => (
            <div key={i} className={`card ${styles.cardSkeleton}`}>
              <div className="skeleton" style={{ height: 20, width: '60%', marginBottom: 12 }} />
              <div className="skeleton" style={{ height: 14, width: '40%', marginBottom: 8 }} />
              <div className="skeleton" style={{ height: 14, width: '80%' }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (cards.length === 0) {
    return (
      <div>
        <h1 className={styles.pageTitle}>Overview</h1>
        <div className="empty-state" style={{ marginBottom: '2rem' }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
          <p>No brands tracked yet. Trigger a live scrape or import a data file below to start tracking your first brand.</p>
        </div>
        <IngestPanel onSuccess={loadData} />
      </div>
    );
  }

  return (
    <div>
      <h1 className={styles.pageTitle}>Overview</h1>
      <p className={styles.subtitle}>{cards.length} brands tracked</p>
      <div className={styles.grid}>
        {cards.map(({ brand, productCount, reviewCount, avgRating, recentScores }) => (
          <Link href={`/dashboard/brands/${brand.id}`} key={brand.id} className={`card ${styles.brandCard}`}>
            <div className={styles.cardHeader}>
              <h3>{brand.name}</h3>
              <Sparkline data={recentScores} color={avgRating >= 4 ? 'var(--sentiment-positive)' : avgRating >= 3 ? 'var(--sentiment-neutral)' : 'var(--sentiment-negative)'} />
            </div>
            <p className={styles.category}>{brand.category}</p>
            <div className={styles.stats}>
              <div className={styles.stat}>
                <span className={styles.statValue}>{productCount}</span>
                <span className={styles.statLabel}>products</span>
              </div>
              <div className={styles.stat}>
                <span className={styles.statValue}>{reviewCount}</span>
                <span className={styles.statLabel}>reviews</span>
              </div>
              <div className={styles.stat}>
                <span className={styles.statValue}>{avgRating}</span>
                <span className={styles.statLabel}>avg rating</span>
              </div>
            </div>
          </Link>
        ))}
      </div>

      <IngestPanel onSuccess={loadData} />
    </div>
  );
}
