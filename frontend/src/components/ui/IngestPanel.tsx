'use client';

import { useState } from 'react';
import styles from './IngestPanel.module.css';

interface IngestPanelProps {
  onSuccess?: () => void;
}

export default function IngestPanel({ onSuccess }: IngestPanelProps) {
  const [activeTab, setActiveTab] = useState<'scrape' | 'import'>('scrape');
  const [brandKey, setBrandKey] = useState('decode_age');
  const [brandName, setBrandName] = useState('');
  const [brandUrl, setBrandUrl] = useState('');
  const [category, setCategory] = useState('wellness');
  const [file, setFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  async function handleScrape(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setStatus({ type: 'info', text: 'Queueing live scrape task in the background...' });

    try {
      const res = await fetch(`${API_BASE}/brands/scrape?brand_key=${brandKey}`, {
        method: 'POST',
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to trigger scrape');

      setStatus({
        type: 'success',
        text: `Success! Scrape task for ${data.brand_name || brandKey} has been queued in the background. Reviews will be cleaned and enriched automatically.`,
      });
      if (onSuccess) {
        // Reload after short delay to let the task begin
        setTimeout(onSuccess, 3000);
      }
    } catch (err: any) {
      setStatus({ type: 'error', text: err.message || 'Scrape failed to trigger.' });
    } finally {
      setLoading(false);
    }
  }

  async function handleImport(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setStatus({ type: 'error', text: 'Please select a file to import.' });
      return;
    }
    if (!brandName.trim()) {
      setStatus({ type: 'error', text: 'Please specify a brand name.' });
      return;
    }

    setLoading(true);
    setStatus({ type: 'info', text: 'Uploading file and processing NLP pipelines...' });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('brand_name', brandName.trim());
      if (brandUrl.trim()) formData.append('brand_url', brandUrl.trim());
      if (category.trim()) formData.append('category', category.trim());

      const res = await fetch(`${API_BASE}/brands/import`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Import failed');

      const s = data.summary;
      setStatus({
        type: 'success',
        text: `Successfully imported "${data.brand.name}"! Created ${s.new_products_created} products, inserted ${s.new_reviews_inserted} new reviews (${s.duplicate_reviews_skipped} duplicates skipped) and completed NLP sentiment and theme enrichment.`,
      });
      
      // Reset file input
      setFile(null);
      setBrandName('');
      setBrandUrl('');

      if (onSuccess) onSuccess();
    } catch (err: any) {
      setStatus({ type: 'error', text: err.message || 'Data import failed.' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.panel}>
      <h2 className={styles.panelTitle}>Add Brand Data</h2>
      <p className={styles.description}>
        Scrape wellness D2C websites directly or import pre-scraped customer reviews and products.
      </p>

      <div className={styles.tabs}>
        <button
          type="button"
          onClick={() => { setActiveTab('scrape'); setStatus(null); }}
          className={`${styles.tab} ${activeTab === 'scrape' ? styles.activeTab : ''}`}
        >
          Live Website Scraper
        </button>
        <button
          type="button"
          onClick={() => { setActiveTab('import'); setStatus(null); }}
          className={`${styles.tab} ${activeTab === 'import' ? styles.activeTab : ''}`}
        >
          Import JSON / CSV File
        </button>
      </div>

      {activeTab === 'scrape' ? (
        <form onSubmit={handleScrape} className={styles.form}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="brand-select">Select Supported Brand</label>
            <select
              id="brand-select"
              value={brandKey}
              onChange={e => setBrandKey(e.target.value)}
              className={styles.select}
              disabled={loading}
            >
              <option value="decode_age">Decode Age (longevity supplements)</option>
              <option value="kapiva">Kapiva (ayurvedic wellness)</option>
              <option value="oziva">OZiva (plant-based nutrition)</option>
            </select>
          </div>
          <div className={styles.actions}>
            <button type="submit" className="btn btn--primary" disabled={loading}>
              {loading ? 'Queueing Scraper...' : 'Trigger Live Scrape'}
            </button>
          </div>
        </form>
      ) : (
        <form onSubmit={handleImport} className={styles.form}>
          <div className={styles.formRow}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="brand-name-input">Brand Name *</label>
              <input
                id="brand-name-input"
                type="text"
                value={brandName}
                onChange={e => setBrandName(e.target.value)}
                placeholder="e.g. Wellbeing Nutrition"
                className={styles.input}
                disabled={loading}
                required
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="category-select">Category</label>
              <select
                id="category-select"
                value={category}
                onChange={e => setCategory(e.target.value)}
                className={styles.select}
                disabled={loading}
              >
                <option value="wellness">Wellness supplements</option>
                <option value="ayurvedic wellness">Ayurvedic wellness</option>
                <option value="plant-based nutrition">Plant-based nutrition</option>
                <option value="cosmetics">Organic cosmetics</option>
              </select>
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="brand-url-input">Brand Website URL (Optional)</label>
            <input
              id="brand-url-input"
              type="url"
              value={brandUrl}
              onChange={e => setBrandUrl(e.target.value)}
              placeholder="https://wellbeingnutrition.com"
              className={styles.input}
              disabled={loading}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Upload Dataset (.csv or .json) *</label>
            <div
              className={`${styles.fileDropArea} ${isDragOver ? styles.fileDropAreaActive : ''}`}
              onDragOver={e => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={e => {
                e.preventDefault();
                setIsDragOver(false);
                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                  setFile(e.dataTransfer.files[0]);
                }
              }}
              onClick={() => document.getElementById('file-upload-input')?.click()}
            >
              <input
                id="file-upload-input"
                type="file"
                accept=".csv,.json"
                style={{ display: 'none' }}
                onChange={e => {
                  if (e.target.files && e.target.files[0]) {
                    setFile(e.target.files[0]);
                  }
                }}
              />
              <span className={styles.fileIcon}>📄</span>
              <span className={styles.fileText}>
                {file ? `Selected file: ${file.name}` : 'Drag & drop your JSON or CSV file here, or click to browse'}
              </span>
            </div>
          </div>

          <div className={styles.actions}>
            <button type="submit" className="btn btn--primary" disabled={loading || !file}>
              {loading ? 'Processing File...' : 'Import Data File'}
            </button>
          </div>
        </form>
      )}

      {status && (
        <div className={`${styles.statusMessage} ${styles[status.type]}`}>
          {status.text}
        </div>
      )}
    </div>
  );
}
