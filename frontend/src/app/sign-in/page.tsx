'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import styles from './auth.module.css';

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Simulate login
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
          <h1 className={styles.title}>Log in to your workspace</h1>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
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
            {loading ? 'Logging in...' : 'Log In'}
          </button>
        </form>

        <div className={styles.divider}>or</div>

        <button onClick={handleBypass} className={`btn btn--secondary ${styles.bypassBtn}`} disabled={loading}>
          Launch with Developer Bypass
        </button>

        <p className={styles.footerText}>
          Don't have an account?
          <Link href="/sign-up" className={styles.footerLink}>
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
