'use client';

import { useState } from 'react';
import { api, SearchResult } from '@/lib/api';
import styles from './search.module.css';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await api.search(query.trim(), 15);
      setResults(data.results);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className={styles.pageTitle}>Search Reviews</h1>
      <p className={styles.subtitle}>Semantic search across all review data</p>

      <form onSubmit={handleSearch} className={styles.searchForm}>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="e.g. complaints about packaging, efficacy of NMN..."
          className={styles.searchInput}
        />
        <button type="submit" className="btn btn--primary" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {loading && (
        <div className={styles.results}>
          {[1, 2, 3].map(i => (
            <div key={i} className="skeleton" style={{ height: 70, marginBottom: 8, borderRadius: 'var(--radius-sm)' }} />
          ))}
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="empty-state">
          <p>No matching reviews found. Try a different query.</p>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className={styles.results}>
          <p className={styles.resultCount}>{results.length} results</p>
          {results.map((r, i) => (
            <article key={i} className={styles.resultCard}>
              <div className={styles.resultMeta}>
                <span className={`badge badge--${r.sentiment}`}>{r.sentiment}</span>
                {r.distance != null && (
                  <span className={styles.score}>relevance: {(1 - r.distance).toFixed(2)}</span>
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
