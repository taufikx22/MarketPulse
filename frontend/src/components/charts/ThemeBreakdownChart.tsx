'use client';

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { ThemeData } from '@/lib/api';

interface Props {
  data: ThemeData[];
}

function scoreToColor(score: number): string {
  if (score > 0.6) return 'var(--sentiment-positive)';
  if (score < 0.4) return 'var(--sentiment-negative)';
  return 'var(--sentiment-neutral)';
}

export default function ThemeBreakdownChart({ data }: Props) {
  if (data.length === 0) {
    return <div className="empty-state"><p>No theme data yet</p></div>;
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(200, data.length * 36)}>
      <BarChart data={data} layout="vertical" margin={{ top: 5, right: 10, left: 80, bottom: 5 }}>
        <XAxis type="number" tick={{ fontSize: 11 }} />
        <YAxis dataKey="theme" type="category" tick={{ fontSize: 12 }} width={80} />
        <Tooltip
          contentStyle={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.8rem',
          }}
          formatter={(value: any, name: any) => [value, name === 'count' ? 'Reviews' : name]}
        />
        <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={20}>
          {data.map((entry, i) => (
            <Cell key={i} fill={scoreToColor(entry.avg_score)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
