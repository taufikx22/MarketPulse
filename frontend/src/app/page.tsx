'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { useTheme } from '@/lib/theme';
import Logo from '@/components/ui/Logo';
import DataBackground from '@/components/ui/DataBackground';
import styles from './landing.module.css';

export default function HomePage() {
  const { theme, toggle } = useTheme();

  useEffect(() => {
    const getElements = () => document.querySelectorAll('.' + styles.reveal);

    const handleScroll = () => {
      const viewportHeight = window.innerHeight;
      getElements().forEach((el) => {
        const rect = el.getBoundingClientRect();
        // If the top of the element enters the screen (with 40px offset)
        if (rect.top < viewportHeight - 40) {
          el.classList.add(styles.revealVisible);
        } else {
          // Remove if it goes back below the fold to allow animated re-entry
          el.classList.remove(styles.revealVisible);
        }
      });
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('resize', handleScroll);
    handleScroll(); // Run once initially

    // Watch for React DOM changes to keep animations synced
    const mutationObserver = new MutationObserver(() => {
      handleScroll();
    });
    mutationObserver.observe(document.body, { childList: true, subtree: true });

    return () => {
      mutationObserver.disconnect();
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleScroll);
    };
  }, []);

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.logo}>
          <Logo size={24} />
          MarketPulse
        </div>
        <div className={styles.actions}>
          <button onClick={toggle} className={styles.themeToggle} aria-label="Toggle theme">
            {theme === 'light' ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
            )}
          </button>
          <Link href="/sign-in" style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)', marginRight: '0.5rem' }}>
            Log In
          </Link>
          <Link href="/sign-up" className="btn btn--primary" style={{ padding: '6px 14px', fontSize: '0.8rem' }}>
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero Fold Wrapper with Loop Background */}
      <div className={styles.heroWrapper}>
        <DataBackground />
        <section className={`${styles.reveal} ${styles.hero}`}>
          <div className={styles.heroLeft}>
            <h1 className={styles.heroTitle}>Marketing & Customer Intelligence for Wellness Brands</h1>
          </div>
          <div className={styles.heroRight}>
            <p className={styles.heroSubtitle}>
              Continuous Shopify ingestion, zero-shot theme tagging, and high-fidelity semantic search. Stop guessing. Track competitor sentiment in real-time.
            </p>
            <div className={styles.heroActions}>
              <Link href="/dashboard" className={`btn btn--primary ${styles.ctaBtn}`}>
                Launch Platform Dashboard
              </Link>
            </div>
          </div>
        </section>
      </div>

      {/* Bento Grid - Reveals on scroll */}
      <section className={`${styles.reveal} ${styles.section}`} style={{ paddingTop: '6rem' }}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionTag}>HOW IT WORKS</span>
          <h2 className={styles.sectionTitle}>Pipeline Architecture</h2>
        </div>

        <div className={styles.bentoGrid}>
          {/* Dominant Card (Ingest & Chart) */}
          <div className={styles.bentoDominant}>
            <div className={styles.bentoInfo}>
              <span className={styles.bentoTag}>01. INGESTION</span>
              <h3 className={styles.bentoTitle}>Direct ingestion of customer reviews.</h3>
              <p className={styles.bentoDesc}>
                Automatically scrape products and reviews from Shopify wellness sites, or drag and drop custom JSON/CSV datasets directly into the platform workspace.
              </p>
            </div>
            
            <div className={styles.ingestionStream}>
              <div className={styles.ingestionRow}>
                <span className={styles.ingestStatusBadge}>✓ SCRAPING COMPLETE</span>
                <span className={styles.ingestSource}>shopify://decode-age/reviews</span>
                <span className={styles.ingestCount}>+148 reviews</span>
              </div>
              <div className={styles.ingestionRow}>
                <span className={styles.ingestStatusBadge}>✓ FILE IMPORTED</span>
                <span className={styles.ingestSource}>raw_feedback_Q3.csv</span>
                <span className={styles.ingestCount}>+2,450 records</span>
              </div>
            </div>

            <div className={styles.chartContainer}>
              <div className={styles.chartScore}>
                <span className={styles.scoreVal}>4.2 ★</span>
                <span className={styles.scoreLabel}>average customer rating</span>
              </div>
              <svg viewBox="0 0 500 120" width="100%" height="120" fill="none" style={{ marginTop: '2.5rem' }}>
                <path d="M 0 100 Q 120 40 250 80 T 500 20" stroke="var(--accent)" strokeWidth="2.5" fill="none" />
                <circle cx="250" cy="80" r="4.5" fill="var(--accent)" />
                <circle cx="500" cy="20" r="4.5" fill="var(--accent)" />
                <line x1="0" y1="110" x2="500" y2="110" stroke="var(--border)" strokeDasharray="3 3" />
                <line x1="0" y1="60" x2="500" y2="60" stroke="var(--border)" strokeDasharray="3 3" />
                <line x1="0" y1="10" x2="500" y2="10" stroke="var(--border)" strokeDasharray="3 3" />
              </svg>
            </div>
          </div>

          {/* Card 2: Cleaning */}
          <div className={styles.bentoCard}>
            <div className={styles.bentoInfo}>
              <span className={styles.bentoTag}>02. DEDUPLICATE</span>
              <h3 className={styles.bentoTitle}>Cleanse and hash raw texts.</h3>
              <p className={styles.bentoDesc}>
                Strips HTML tags, collapses whitespace, filters out non-English reviews, and hashes text to bypass duplicates.
              </p>
            </div>
            
            <div className={styles.compareRow}>
              <div className={styles.rawText}>&lt;p&gt;stomach issues initially... &lt;/p&gt;</div>
              <div className={styles.cleanText}>stomach issues initially...</div>
              <div className={styles.hashVal}>sha256_e8179f...</div>
            </div>
          </div>

          {/* Card 3: NLP Classify */}
          <div className={styles.bentoCard}>
            <div className={styles.bentoInfo}>
              <span className={styles.bentoTag}>03. NLP CATEGORIZE</span>
              <h3 className={styles.bentoTitle}>Zero-shot theme classification.</h3>
              <p className={styles.bentoDesc}>
                Auto-tags sentiment labels and classifies customer comments against zero-shot themes without manual training.
              </p>
            </div>

            <div className={styles.themeList}>
              <div className={styles.themeRow}>
                <span className={styles.themeLabel}>efficacy</span>
                <div className={styles.themeBar}><div className={styles.themeBarFill} style={{ width: '88%' }} /></div>
                <span className={styles.themeRatio}>88%</span>
              </div>
              <div className={styles.themeRow}>
                <span className={styles.themeLabel}>taste/flavor</span>
                <div className={styles.themeBar}><div className={styles.themeBarFill} style={{ width: '92%' }} /></div>
                <span className={styles.themeRatio}>92%</span>
              </div>
              <div className={styles.themeRow}>
                <span className={styles.themeLabel}>packaging</span>
                <div className={styles.themeBar}><div className={styles.themeBarFill} style={{ width: '40%' }} /></div>
                <span className={styles.themeRatio}>40%</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Mock Dashboard Preview - Reveals on scroll */}
      <section className={`${styles.reveal} ${styles.section} ${styles.sectionInsights}`} style={{ paddingTop: '4rem' }}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionTag}>DATA INSIGHTS</span>
          <h2 className={styles.sectionTitle}>High-Fidelity Interface</h2>
        </div>

        <div className={styles.insightsSplit}>
          {/* Left Column: Console Preview */}
          <div className={styles.previewContainer}>
            <div className={styles.previewHeader}>
              <div className={styles.previewDot} />
              <div className={styles.previewDot} />
              <div className={styles.previewDot} />
              <span className={styles.previewTitle}>MarketPulse Console — Preview Mode</span>
            </div>
            <div className={styles.previewBody}>
              <div className={styles.previewSidebar}>
                <div className={styles.previewSidebarItem} />
                <div className={styles.previewSidebarItem} />
                <div className={styles.previewSidebarItem} />
                <div className={styles.previewSidebarItem} />
              </div>
              <div className={styles.previewContent}>
                <div className={styles.previewCardGrid}>
                  <div className={styles.previewMiniCard}>
                    <span className={styles.previewMiniTitle}>Decode Age</span>
                    <span className={styles.previewMiniStat}>4.2 ★</span>
                    <div className={styles.previewSpark} />
                  </div>
                  <div className={styles.previewMiniCard}>
                    <span className={styles.previewMiniTitle}>Kapiva</span>
                    <span className={styles.previewMiniStat}>3.9 ★</span>
                    <div className={styles.previewSpark} />
                  </div>
                  <div className={styles.previewMiniCard}>
                    <span className={styles.previewMiniTitle}>OZiva</span>
                    <span className={styles.previewMiniStat}>4.1 ★</span>
                    <div className={styles.previewSpark} />
                  </div>
                </div>
                <div className="card" style={{ padding: '1rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Automated Analyst Note</span>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    "Efficacy mentions are highly positive (82% positive) for Decode Age, driven by sustained energy and sleep improvements. Packaging complaints rose slightly this month."
                  </p>
                </div>
                
                <div className="card" style={{ padding: '1rem', marginTop: '1rem', background: 'var(--bg-surface-hover)', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Theme Sentiment Breakdown</span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.75rem' }}>
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                        <span>Efficacy (Decode Age)</span>
                        <span style={{ color: 'var(--accent)', fontWeight: 600 }}>82% Positive</span>
                      </div>
                      <div style={{ height: '6px', background: 'var(--border)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: '82%', background: 'var(--accent)' }} />
                      </div>
                    </div>
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                        <span>Packaging (Complaints)</span>
                        <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>60% Negative</span>
                      </div>
                      <div style={{ height: '6px', background: 'var(--border)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: '60%', background: '#ff3b30' }} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Semantic Search Mockup [NEW] */}
          <div className={styles.queryMockup}>
            <div className={styles.queryMockupHeader}>
              <span className={styles.bentoTag}>SEMANTIC VECTOR SEARCH</span>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>SEARCH QUERY INPUT</span>
              <div className={styles.queryInput}>Query: "sleep quality, fatigue, ashwagandha"</div>
            </div>

            <div className={styles.queryResultsList}>
              <div className={styles.queryResultItem}>
                <div className={styles.queryResultMeta}>
                  <span>Decode Age NMN</span>
                  <span className={styles.queryResultScore}>92% match</span>
                </div>
                <p className={styles.queryResultText}>
                  "Been taking NMN for 3 weeks. Morning fatigue is gone, and my sleep app shows deep sleep increased by 40 mins."
                </p>
              </div>

              <div className={styles.queryResultItem}>
                <div className={styles.queryResultMeta}>
                  <span>Kapiva Ashwagandha</span>
                  <span className={styles.queryResultScore}>86% match</span>
                </div>
                <p className={styles.queryResultText}>
                  "Helps calm my mind before sleep, but the taste is slightly bitter. Definitely notice less tossing and turning."
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing - Reveals on scroll */}
      <section className={`${styles.reveal} ${styles.section}`} style={{ paddingTop: '4rem', paddingBottom: '8rem' }}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionTag}>PRICING PLAN</span>
          <h2 className={styles.sectionTitle}>Transparent Pricing</h2>
        </div>

        <div className={styles.pricingGrid}>
          {/* Plan 1: Free */}
          <div className={styles.pricingCard}>
            <h3 className={styles.pricingTier}>Starter</h3>
            <div className={styles.pricingCost}>$0<span style={{ fontSize: '1rem', fontWeight: 'normal', color: 'var(--text-tertiary)' }}>/mo</span></div>
            <ul className={styles.pricingFeatures}>
              <li className={styles.pricingFeature}>Track 1 wellness brand</li>
              <li className={styles.pricingFeature}>Local SQLite database store</li>
              <li className={styles.pricingFeature}>Basic automated insights</li>
              <li className={styles.pricingFeature}>Semantic search query limits</li>
            </ul>
            <Link href="/dashboard" className={`btn btn--secondary ${styles.pricingBtn}`}>
              Get Started Free
            </Link>
          </div>

          {/* Plan 2: Professional [NEW] */}
          <div className={styles.pricingCard}>
            <h3 className={styles.pricingTier}>Professional</h3>
            <div className={styles.pricingCost}>$19<span style={{ fontSize: '1rem', fontWeight: 'normal', color: 'var(--text-tertiary)' }}>/mo</span></div>
            <ul className={styles.pricingFeatures}>
              <li className={styles.pricingFeature}>Track up to 3 wellness brands</li>
              <li className={styles.pricingFeature}>Custom CSV/JSON ingestion panel</li>
              <li className={styles.pricingFeature}>Full semantic search access</li>
              <li className={styles.pricingFeature}>Email alerts for negative spikes</li>
            </ul>
            <Link href="/dashboard" className={`btn btn--secondary ${styles.pricingBtn}`}>
              Start Professional Trial
            </Link>
          </div>

          {/* Plan 3: Business */}
          <div className={`${styles.pricingCard} ${styles.premiumPricing}`}>
            <h3 className={styles.pricingTier}>Business</h3>
            <div className={styles.pricingCost}>$99<span style={{ fontSize: '1rem', fontWeight: 'normal', color: 'var(--text-tertiary)' }}>/mo</span></div>
            <ul className={styles.pricingFeatures}>
              <li className={styles.pricingFeature}>Track unlimited wellness brands</li>
              <li className={styles.pricingFeature}>Dedicated production PostgreSQL</li>
              <li className={styles.pricingFeature}>Advanced zero-shot analytical logs</li>
              <li className={styles.pricingFeature}>Workspace API token access</li>
            </ul>
            <Link href="/dashboard" className={`btn btn--primary ${styles.pricingBtn}`}>
              Start Business Trial
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={`${styles.reveal} ${styles.footer}`}>
        <div>© 2026 MarketPulse Inc. All rights reserved. Built with Next.js, FastAPI, and ChromaDB.</div>
        <div className={styles.footerLinks}>
          <a href="https://github.com" target="_blank" rel="noreferrer">GitHub Project</a>
          <a href="/dashboard">Console Dashboard</a>
        </div>
      </footer>
    </div>
  );
}
