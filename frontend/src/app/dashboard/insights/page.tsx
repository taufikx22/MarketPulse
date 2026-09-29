'use client';

import { useEffect, useState } from 'react';
import { api, Insight, Brand } from '@/lib/api';
import styles from './insights.module.css';

export default function InsightsPage() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [filterBrand, setFilterBrand] = useState<number | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>('');
  const [viewTab, setViewTab] = useState<'all' | 'anomalies' | 'general'>('all');
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [expandedIds, setExpandedIds] = useState<number[]>([]);

  useEffect(() => {
    api.brands().then(setBrands).catch(console.error);
  }, []);

  const fetchInsights = () => {
    setLoading(true);
    const opts: { brandId?: number; severity?: string; isAnomaly?: boolean } = {};
    if (filterBrand) opts.brandId = filterBrand;
    if (filterSeverity) opts.severity = filterSeverity;
    if (viewTab === 'anomalies') opts.isAnomaly = true;
    if (viewTab === 'general') opts.isAnomaly = false;

    api.insights(opts)
      .then(setInsights)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchInsights();
  }, [filterBrand, filterSeverity, viewTab]);

  const handleRunDetection = async () => {
    setDetecting(true);
    try {
      await api.detectAnomalies(filterBrand || undefined);
      fetchInsights();
    } catch (err) {
      console.error('Failed to run anomaly detection:', err);
    } finally {
      setDetecting(false);
    }
  };

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

  const getSeverityBadgeClass = (severity?: string) => {
    switch (severity) {
      case 'critical': return styles.badgeCritical;
      case 'high': return styles.badgeHigh;
      case 'medium': return styles.badgeMedium;
      case 'low': return styles.badgeLow;
      default: return 'badge badge--neutral';
    }
  };

  const getCardBorderClass = (insight: Insight) => {
    if (!insight.metric) return '';
    switch (insight.severity) {
      case 'critical': return styles.anomalyCardCritical;
      case 'high': return styles.anomalyCardHigh;
      case 'medium': return styles.anomalyCardMedium;
      case 'low': return styles.anomalyCardLow;
      default: return '';
    }
  };

  return (
    <div>
      <div className={styles.controlsHeader}>
        <div>
          <h1 className={styles.pageTitle}>Analytical Insights & Controls</h1>
          <p style={{ color: 'var(--text-tertiary)', fontSize: '0.85rem', marginTop: '-0.5rem' }}>
            Explainable anomaly detection, statistical sentiment spikes, and customer experience drivers.
          </p>
        </div>
        <div className={styles.headerActions}>
          <button
            onClick={handleRunDetection}
            disabled={detecting}
            className="btn btn--primary"
            style={{ fontSize: '0.85rem' }}
          >
            {detecting ? 'Analyzing...' : 'Detect Anomalies Now'}
          </button>
        </div>
      </div>

      <div className={styles.filters}>
        <button
          onClick={() => setFilterBrand(null)}
          className={`btn ${!filterBrand ? 'btn--primary' : 'btn--secondary'}`}
        >
          All Brands
        </button>
        {brands.map(b => (
          <button
            key={b.id}
            onClick={() => setFilterBrand(b.id)}
            className={`btn ${filterBrand === b.id ? 'btn--primary' : 'btn--secondary'}`}
          >
            {b.name}
          </button>
        ))}
      </div>

      <div className={styles.subFilters}>
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            onClick={() => setViewTab('all')}
            className={`btn ${viewTab === 'all' ? 'btn--primary' : 'btn--secondary'}`}
            style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
          >
            All Feed
          </button>
          <button
            onClick={() => setViewTab('anomalies')}
            className={`btn ${viewTab === 'anomalies' ? 'btn--primary' : 'btn--secondary'}`}
            style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
          >
            Anomalies & Controls Only
          </button>
          <button
            onClick={() => setViewTab('general')}
            className={`btn ${viewTab === 'general' ? 'btn--primary' : 'btn--secondary'}`}
            style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
          >
            General Insights
          </button>
        </div>

        <select
          value={filterSeverity}
          onChange={e => setFilterSeverity(e.target.value)}
          className={styles.filterSelect}
          style={{ marginLeft: 'auto' }}
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {loading ? (
        <div>
          {[1, 2, 3].map(i => (
            <div key={i} className="skeleton" style={{ height: 120, marginBottom: 12, borderRadius: 'var(--radius-sm)' }} />
          ))}
        </div>
      ) : insights.length === 0 ? (
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
          <p>No records matching current filters. Click &quot;Detect Anomalies Now&quot; to evaluate customer review telemetry.</p>
        </div>
      ) : (
        <div className={styles.feed}>
          {insights.map(insight => {
            const hasReviews = insight.supporting_reviews && insight.supporting_reviews.length > 0;
            const isExpanded = expandedIds.includes(insight.id);
            const isAnomaly = !!insight.metric;

            return (
              <article
                key={insight.id}
                className={`${styles.insightCard} ${getCardBorderClass(insight)}`}
              >
                <div className={styles.insightMeta}>
                  {isAnomaly ? (
                    <span className={getSeverityBadgeClass(insight.severity)}>
                      {insight.severity || 'Medium'} Severity
                    </span>
                  ) : null}

                  <span className={`badge badge--${insight.type === 'positive_trend' ? 'positive' : insight.type === 'negative_trend' || insight.type.includes('spike') || insight.type.includes('deterioration') ? 'negative' : 'neutral'}`}>
                    {insight.type.replace(/_/g, ' ')}
                  </span>

                  <span className={styles.brand}>{brandName(insight.brand_id)}</span>
                  <span className={styles.date}>{new Date(insight.generated_at).toLocaleDateString()}</span>
                </div>

                <p className={styles.insightText}>{insight.text}</p>

                {isAnomaly && (
                  <div className={styles.metricGrid}>
                    <div className={styles.metricItem}>
                      <span className={styles.metricLabel}>Metric</span>
                      <span className={styles.metricValue} style={{ fontSize: '0.8rem' }}>
                        {insight.metric?.replace(/_/g, ' ')}
                      </span>
                    </div>
                    {insight.baseline_value != null && (
                      <div className={styles.metricItem}>
                        <span className={styles.metricLabel}>Baseline</span>
                        <span className={styles.metricValue}>
                          {insight.metric?.includes('rating') ? `${insight.baseline_value.toFixed(1)}★` : `${insight.baseline_value}%`}
                        </span>
                      </div>
                    )}
                    {insight.current_value != null && (
                      <div className={styles.metricItem}>
                        <span className={styles.metricLabel}>Current</span>
                        <span className={styles.metricValue}>
                          {insight.metric?.includes('rating') ? `${insight.current_value.toFixed(1)}★` : `${insight.current_value}%`}
                        </span>
                      </div>
                    )}
                    {insight.deviation != null && (
                      <div className={styles.metricItem}>
                        <span className={styles.metricLabel}>Deviation</span>
                        <span className={`${styles.metricValue} ${insight.deviation > 0 && !insight.metric?.includes('rating') ? styles.metricDeviationSpike : insight.deviation < 0 ? styles.metricDeviationDrop : styles.metricDeviationGood}`}>
                          {insight.deviation > 0 ? `+${insight.deviation}` : insight.deviation}
                          {insight.metric?.includes('rating') ? '★' : ' pp'}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {hasReviews && (
                  <>
                    <button
                      onClick={() => toggleExpand(insight.id)}
                      className={styles.toggleReviewsBtn}
                    >
                      {isExpanded ? 'Hide' : 'Drill down into'} supporting evidence ({insight.supporting_reviews?.length} reviews)
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
