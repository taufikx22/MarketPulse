'use client';

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import type { SentimentTrend } from '@/lib/api';

interface Props {
  data: SentimentTrend[];
}

export default function SentimentTrendChart({ data }: Props) {
  // Pivot data: group by week, columns for each sentiment's avg_score
  const weekMap = new Map<string, Record<string, number>>();
  for (const d of data) {
    const weekLabel = d.week.slice(0, 10);
    if (!weekMap.has(weekLabel)) weekMap.set(weekLabel, { week: weekLabel } as any);
    const entry = weekMap.get(weekLabel)!;
    (entry as any)[d.sentiment] = d.avg_score;
    (entry as any)[`${d.sentiment}_count`] = d.count;
  }
  const chartData = Array.from(weekMap.values());

  if (chartData.length === 0) {
    return <div className="empty-state"><p>No sentiment data yet</p></div>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="week" tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
        <Tooltip
          contentStyle={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.8rem',
          }}
        />
        <Line type="monotone" dataKey="positive" stroke="var(--sentiment-positive)" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="negative" stroke="var(--sentiment-negative)" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="neutral" stroke="var(--sentiment-neutral)" strokeWidth={1.5} dot={false} strokeDasharray="4 4" />
      </LineChart>
    </ResponsiveContainer>
  );
}
