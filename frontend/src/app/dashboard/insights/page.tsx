'use client';

import { useEffect, useState } from 'react';
import { api, Insight, Brand } from '@/lib/api';
import styles from './insights.module.css';

export default function InsightsPage() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [filterBrand, setFilterBrand] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedIds, setExpandedIds] = useState<number[]>([]);

  useEffect(() => {
    api.brands().then(setBrands).catch(console.error);
  }, []);

  useEffect(() => {
    setLoading(true);
    api.insights(filterBrand || undefined)
      .then(setInsights)
      .finally(() => setLoading(false));
  }, [filterBrand]);

  const brandName = (id: number) => brands.find(b => b.id === id)?.name || `Brand ${id}`;

  const toggleExpand = (id: number) => {
    setExpandedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const renderStars = (rating: number | null) => {
    if (rating == null) return null;
    return '★'.repeat(rating) + '☆'.repeat(5 - rating);
  };

  if (loading) {
    return (
      <div>
        <h1 className={styles.pageTitle}>Insights</h1>
        {[1, 2, 3].map(i => (
          <div key={i} className="skeleton" style={{ height: 100, marginBottom: 12, borderRadius: 'var(--radius-sm)' }} />
        ))}
      </div>
    );
  }

  return (
    <div>
      <h1 className={styles.pageTitle}>Insights</h1>
      <div className={styles.filters}>
        <button onClick={() => setFilterBrand(null)} className={`btn ${!filterBrand ? 'btn--primary' : 'btn--secondary'}`}>All</button>
        {brands.map(b => (
          <button key={b.id} onClick={() => setFilterBrand(b.id)} className={`btn ${filterBrand === b.id ? 'btn--primary' : 'btn--secondary'}`}>
            {b.name}
          </button>
        ))}
      </div>

      {insights.length === 0 ? (
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
          <p>No insights generated yet. Run the scraping or file import pipeline to generate automated customer insights.</p>
        </div>
      ) : (
        <div className={styles.feed}>
          {insights.map(insight => {
            const hasReviews = insight.supporting_reviews && insight.supporting_reviews.length > 0;
            const isExpanded = expandedIds.includes(insight.id);

            return (
              <article key={insight.id} className={styles.insightCard}>
                <div className={styles.insightMeta}>
                  <span className={`badge badge--${insight.type === 'positive_trend' ? 'positive' : insight.type === 'negative_trend' ? 'negative' : 'neutral'}`}>
                    {insight.type.replace(/_/g, ' ')}
                  </span>
                  <span className={styles.brand}>{brandName(insight.brand_id)}</span>
                  <span className={styles.date}>{new Date(insight.generated_at).toLocaleDateString()}</span>
                </div>
                <p className={styles.insightText}>{insight.text}</p>
                
                {hasReviews && (
                  <>
                    <button
                      onClick={() => toggleExpand(insight.id)}
                      className={styles.toggleReviewsBtn}
                    >
                      {isExpanded ? 'Hide' : 'View'} supporting reviews ({insight.supporting_reviews?.length})
                      <span>{isExpanded ? '▲' : '▼'}</span>
                    </button>
                    
                    {isExpanded && (
                      <div className={styles.supportingReviews}>
                        {insight.supporting_reviews?.map(rev => (
                          <div key={rev.id} className={styles.reviewItem}>
                            <div className={styles.reviewMeta}>
                              {rev.rating != null && (
                                <span style={{ color: '#fbbf24', letterSpacing: '1px' }}>
                                  {renderStars(rev.rating)}
                                </span>
                              )}
                              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                                {rev.author || 'Anonymous'}
                              </span>
                              {rev.review_date && (
                                <span style={{ color: 'var(--text-tertiary)', fontSize: '0.75rem' }}>
                                  {new Date(rev.review_date).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                            <p className={styles.reviewText}>{rev.cleaned_text || rev.raw_text}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}

