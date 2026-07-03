'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import styles from '../sign-in/auth.module.css';

export default function SignUpPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [company, setCompany] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Simulate sign up
    setTimeout(() => {
      setLoading(false);
      router.push('/dashboard');
    }, 1000);
  };

  const handleBypass = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      router.push('/dashboard');
    }, 500);
  };

  return (
    <div className={styles.container}>
      <div className={styles.authCard}>
        <div className={styles.header}>
          <div className={styles.logo}>
            <span className={styles.logoMark}>◆</span>
            MarketPulse
          </div>
          <h1 className={styles.title}>Create your workspace</h1>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="name-input">Full Name</label>
            <input
              id="name-input"
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="John Doe"
              className={styles.input}
              required
              disabled={loading}
            />
          </div>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="email-input">Email address</label>
            <input
              id="email-input"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="name@company.com"
              className={styles.input}
              required
              disabled={loading}
            />
          </div>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="company-input">Company / Workspace Name</label>
            <input
              id="company-input"
              type="text"
              value={company}
              onChange={e => setCompany(e.target.value)}
              placeholder="Acme Wellness Corp"
              className={styles.input}
              required
              disabled={loading}
            />
          </div>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="password-input">Password</label>
            <input
              id="password-input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              className={styles.input}
              required
              disabled={loading}
            />
          </div>

          <button type="submit" className="btn btn--primary" style={{ width: '100%', justifyContent: 'center', padding: '10px 0' }} disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <div className={styles.divider}>or</div>

        <button onClick={handleBypass} className={`btn btn--secondary ${styles.bypassBtn}`} disabled={loading}>
          Launch with Developer Bypass
        </button>

        <p className={styles.footerText}>
          Already have an account?
          <Link href="/sign-in" className={styles.footerLink}>
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
