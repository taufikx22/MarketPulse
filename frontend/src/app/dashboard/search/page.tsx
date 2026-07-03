'use client';

import { useState, useEffect } from 'react';
import { api, SearchResult, Brand } from '@/lib/api';
import styles from './search.module.css';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [brands, setBrands] = useState<Brand[]>([]);
  const [selectedBrand, setSelectedBrand] = useState<number | undefined>(undefined);
  const [selectedSentiment, setSelectedSentiment] = useState<string | undefined>(undefined);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    api.brands().then(setBrands).catch(console.error);
  }, []);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    await performSearch();
  }

  // Trigger search on filter changes if already searched once
  useEffect(() => {
    if (searched && query.trim()) {
      performSearch();
    }
  }, [selectedBrand, selectedSentiment]);

  async function performSearch() {
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await api.search(
        query.trim(),
        selectedBrand,
        selectedSentiment || undefined,
        15
      );
      setResults(data.results);
    } catch (err) {
      console.error(err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  const renderStars = (rating: number | undefined) => {
    if (rating == null) return null;
    return '★'.repeat(rating) + '☆'.repeat(Math.max(0, 5 - rating));
  };

  return (
    <div>
      <h1 className={styles.pageTitle}>Search Reviews</h1>
      <p className={styles.subtitle}>Semantic search across all review data</p>

      <form onSubmit={handleSearch} className={styles.searchForm}>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="e.g. complaints about packaging, efficacy of Shilajit..."
          className={styles.searchInput}
        />
        <button type="submit" className="btn btn--primary" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      <div className={styles.filters}>
        <select
          value={selectedBrand || ''}
          onChange={e => setSelectedBrand(e.target.value ? Number(e.target.value) : undefined)}
          className={styles.filterSelect}
          disabled={loading}
        >
          <option value="">All Brands</option>
          {brands.map(b => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>

        <select
          value={selectedSentiment || ''}
          onChange={e => setSelectedSentiment(e.target.value || undefined)}
          className={styles.filterSelect}
          disabled={loading}
        >
          <option value="">All Sentiments</option>
          <option value="positive">Positive</option>
          <option value="neutral">Neutral</option>
          <option value="negative">Negative</option>
        </select>
      </div>

      {loading && (
        <div className={styles.results}>
          {[1, 2, 3].map(i => (
            <div key={i} className="skeleton" style={{ height: 100, marginBottom: 12, borderRadius: 'var(--radius-sm)' }} />
          ))}
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="empty-state">
          <p>No matching reviews found. Try a different query or adjust your filters.</p>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className={styles.results}>
          <p className={styles.resultCount}>{results.length} results</p>
          {results.map((r, i) => (
            <article key={i} className={styles.resultCard}>
              <div className={styles.resultMeta}>
                <span className={`badge badge--${r.sentiment}`}>{r.sentiment}</span>
                {r.rating != null && (
                  <span className={styles.rating}>{renderStars(r.rating)}</span>
                )}
                {r.product_name && (
                  <span className={styles.productName}>{r.product_name}</span>
                )}
                {r.distance != null && (
                  <span className={styles.score}>relevance: {Math.round((1 - r.distance) * 100)}%</span>
                )}
                {(r.author || r.date) && (
                  <span className={styles.authorDate}>
                    {r.author || 'Anonymous'} • {r.date || 'unknown date'}
                  </span>
                )}
              </div>
              <p className={styles.resultText}>{r.text}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

