import React from 'react';
import { TalentTrendPoint } from '../../types/analytics.types';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { cn } from '../../lib/utils';

interface TalentTrendChartProps {
  data: TalentTrendPoint[];
  height?: number;
  className?: string;
}

export const TalentTrendChart: React.FC<TalentTrendChartProps> = ({
  data,
  height = 280,
  className,
}) => {
  return (
    <div className={cn('w-full', className)}>
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorTech" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3157D5" stopOpacity={0.6} />
                <stop offset="95%" stopColor="#3157D5" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorCreative" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#7657D6" stopOpacity={0.6} />
                <stop offset="95%" stopColor="#7657D6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
            <XAxis dataKey="cohort" tick={{ fill: '#64748B', fontSize: 11 }} />
            <YAxis tick={{ fill: '#64748B', fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0F172A',
                border: 'none',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '12px',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
            <Area
              type="monotone"
              dataKey="technology"
              name="Teknologi"
              stroke="#3157D5"
              fillOpacity={1}
              fill="url(#colorTech)"
            />
            <Area
              type="monotone"
              dataKey="creative"
              name="Kreatif & Desain"
              stroke="#7657D6"
              fillOpacity={1}
              fill="url(#colorCreative)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
