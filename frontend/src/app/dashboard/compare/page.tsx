'use client';

import { useEffect, useState } from 'react';
import { api, Brand, ComparisonData } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import styles from './compare.module.css';

export default function ComparePage() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [data, setData] = useState<ComparisonData[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.brands().then(setBrands);
  }, []);

  useEffect(() => {
    if (selected.length >= 2) {
      setLoading(true);
      api.compare(selected).then(setData).finally(() => setLoading(false));
    } else {
      setData([]);
    }
  }, [selected]);

  const toggleBrand = (id: number) => {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : prev.length < 4 ? [...prev, id] : prev
    );
  };

  // Auto-select first 2 brands
  useEffect(() => {
    if (brands.length >= 2 && selected.length === 0) {
      setSelected(brands.slice(0, Math.min(3, brands.length)).map(b => b.id));
    }
  }, [brands]);

  const sentimentChartData = data.map(d => ({
    name: d.brand_name,
    positive: d.sentiment['positive'] || 0,
    negative: d.sentiment['negative'] || 0,
    neutral: d.sentiment['neutral'] || 0,
  }));

  return (
    <div>
      <h1 className={styles.pageTitle}>Compare Brands</h1>

      <div className={styles.selector}>
        {brands.map(b => (
          <button
            key={b.id}
            onClick={() => toggleBrand(b.id)}
            className={`btn ${selected.includes(b.id) ? 'btn--primary' : 'btn--secondary'}`}
          >
            {b.name}
          </button>
        ))}
      </div>

      {selected.length < 2 && (
        <div className="empty-state">
          <p>Select at least 2 brands to compare</p>
        </div>
      )}

      {loading && (
        <div className={styles.grid}>
          <div className="skeleton" style={{ height: 300 }} />
        </div>
      )}

      {data.length >= 2 && !loading && (
        <>
          <div className={styles.grid}>
            <section className="card">
              <h2 className={styles.sectionTitle}>Sentiment Distribution</h2>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={sentimentChartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem' }} />
                  <Legend />
                  <Bar dataKey="positive" fill="var(--sentiment-positive)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="neutral" fill="var(--sentiment-neutral)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="negative" fill="var(--sentiment-negative)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </section>
          </div>

          <section className={styles.tableSection}>
            <h2 className={styles.sectionTitle}>Side-by-Side Metrics</h2>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Metric</th>
                  {data.map(d => <th key={d.brand_id}>{d.brand_name}</th>)}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Products</td>
                  {data.map(d => <td key={d.brand_id}>{d.product_count}</td>)}
                </tr>
                <tr>
                  <td>Reviews</td>
                  {data.map(d => <td key={d.brand_id}>{d.review_count}</td>)}
                </tr>
                <tr>
                  <td>Avg Rating</td>
                  {data.map(d => <td key={d.brand_id}>{d.avg_rating}</td>)}
                </tr>
                <tr>
                  <td>Avg Price</td>
                  {data.map(d => <td key={d.brand_id}>₹{d.avg_price.toLocaleString()}</td>)}
                </tr>
                <tr>
                  <td>Top Theme</td>
                  {data.map(d => <td key={d.brand_id}>{d.top_themes[0]?.theme || '—'}</td>)}
                </tr>
              </tbody>
            </table>
          </section>
        </>
      )}
    </div>
  );
}
