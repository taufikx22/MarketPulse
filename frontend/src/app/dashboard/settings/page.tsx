'use client';

import { useEffect, useState } from 'react';
import { api, Brand } from '@/lib/api';

interface UserInfo {
  name: string;
  email: string;
  role: string;
  orgName: string;
}

export default function SettingsPage() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [tokenCopied, setTokenCopied] = useState(false);

  const mockUser: UserInfo = {
    name: 'Mock Analyst',
    email: 'mock@marketpulse.dev',
    role: 'Workspace Administrator',
    orgName: 'Mock Workspace',
  };

  useEffect(() => {
    api.brands()
      .then(setBrands)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleCopyToken = () => {
    setTokenCopied(true);
    setTimeout(() => setTokenCopied(false), 2000);
  };

  return (
    <div style={{ maxWidth: '800px' }}>
      <h1 style={{ marginBottom: '0.25rem' }}>Workspace Settings</h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '2rem' }}>
        Manage your user account, workspace organization settings, and database configurations.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        {/* User Card */}
        <section className="card">
          <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
            User Account Details
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.9rem' }}>
            <div>
              <span style={{ color: 'var(--text-tertiary)', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>FULL NAME</span>
              <strong style={{ color: 'var(--text-primary)' }}>{mockUser.name}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-tertiary)', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>EMAIL ADDRESS</span>
              <strong style={{ color: 'var(--text-primary)' }}>{mockUser.email}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-tertiary)', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>ROLE</span>
              <strong style={{ color: 'var(--text-primary)' }}>{mockUser.role}</strong>
            </div>
          </div>
        </section>

        {/* Organization Card */}
        <section className="card">
          <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
            Organization Workspace
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.9rem' }}>
            <div>
              <span style={{ color: 'var(--text-tertiary)', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>ORGANIZATION NAME</span>
              <strong style={{ color: 'var(--text-primary)' }}>{mockUser.orgName}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-tertiary)', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>ACTIVE TRACKED BRANDS</span>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                {loading ? (
                  <span className="skeleton" style={{ width: '80px', height: '20px' }} />
                ) : brands.length === 0 ? (
                  <span style={{ color: 'var(--text-tertiary)', fontSize: '0.85rem' }}>No brands added yet.</span>
                ) : (
                  brands.map(b => (
                    <span
                      key={b.id}
                      className="badge badge--neutral"
                      style={{ padding: '4px 10px', borderRadius: '4px', fontSize: '0.8rem' }}
                    >
                      {b.name}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Dev Environment Configs */}
        <section className="card">
          <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
            System Configurations & API Tokens
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', fontSize: '0.9rem' }}>
            <div>
              <span style={{ color: 'var(--text-tertiary)', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>ACTIVE DATABASE DIALECT</span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', marginTop: '0.25rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }} />
                SQLite Local Store (marketpulse.db)
              </span>
            </div>
            <div>
              <span style={{ color: 'var(--text-tertiary)', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>DEVELOPMENT API TOKEN</span>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.35rem' }}>
                <input
                  type="password"
                  value="mp_live_token_77a942fb882194cc2"
                  readOnly
                  style={{
                    flex: 1,
                    background: 'var(--bg-surface-hover)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '8px 12px',
                    fontFamily: 'monospace',
                    fontSize: '0.85rem',
                    color: 'var(--text-secondary)',
                    outline: 'none',
                  }}
                />
                <button onClick={handleCopyToken} className="btn btn--secondary">
                  {tokenCopied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
