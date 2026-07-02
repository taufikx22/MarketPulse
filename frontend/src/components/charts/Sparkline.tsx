'use client';

import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface Props {
  data: number[];
  color?: string;
}

export default function Sparkline({ data, color = 'var(--accent)' }: Props) {
  const chartData = data.map((value, i) => ({ v: value }));

  return (
    <ResponsiveContainer width={80} height={28}>
      <LineChart data={chartData}>
        <Line type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
