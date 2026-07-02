'use client';

import { useEffect, useState } from 'react';
import { api, Insight, Brand } from '@/lib/api';
import styles from './insights.module.css';

export default function InsightsPage() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [filterBrand, setFilterBrand] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.brands().then(setBrands);
  }, []);

  useEffect(() => {
    setLoading(true);
    api.insights(filterBrand || undefined)
      .then(setInsights)
      .finally(() => setLoading(false));
  }, [filterBrand]);

  const brandName = (id: number) => brands.find(b => b.id === id)?.name || `Brand ${id}`;

  if (loading) {
    return (
      <div>
        <h1 className={styles.pageTitle}>Insights</h1>
        {[1, 2, 3].map(i => (
          <div key={i} className="skeleton" style={{ height: 60, marginBottom: 8, borderRadius: 'var(--radius-sm)' }} />
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
          <p>No insights generated yet. Run the enrichment pipeline to generate automated analysis.</p>
        </div>
      ) : (
        <div className={styles.feed}>
          {insights.map(insight => (
            <article key={insight.id} className={styles.insightCard}>
              <div className={styles.insightMeta}>
                <span className={`badge badge--${insight.type === 'positive_trend' ? 'positive' : insight.type === 'negative_trend' ? 'negative' : 'neutral'}`}>
                  {insight.type.replace(/_/g, ' ')}
                </span>
                <span className={styles.brand}>{brandName(insight.brand_id)}</span>
                <span className={styles.date}>{new Date(insight.generated_at).toLocaleDateString()}</span>
              </div>
              <p className={styles.insightText}>{insight.text}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
