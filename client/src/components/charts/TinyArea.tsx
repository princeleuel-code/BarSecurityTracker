import { useMemo } from 'react';
import { Area, AreaChart, ResponsiveContainer } from 'recharts';

interface TinyAreaProps {
  data: number[];
  color?: string;
  className?: string;
}

export function TinyArea({ data, color = '#10b981', className }: TinyAreaProps) {
  // Format data for Recharts
  const chartData = useMemo(() => {
    return data.map((value, index) => ({
      value,
      index
    }));
  }, [data]);

  return (
    <div className={className} style={{ width: '100%', height: '48px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{
            top: 2,
            right: 0,
            left: 0,
            bottom: 2,
          }}
        >
          <defs>
            <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.2}/>
              <stop offset="95%" stopColor={color} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            fill="url(#colorGradient)"
            strokeWidth={1.5}
            dot={false}
            animationDuration={300}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}