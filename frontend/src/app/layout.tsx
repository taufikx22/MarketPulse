import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'MarketPulse — Wellness Brand Intelligence',
  description: 'Competitor & customer intelligence for wellness and D2C brands',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
