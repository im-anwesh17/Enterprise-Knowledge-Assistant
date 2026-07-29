import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line
} from 'recharts';

interface DynamicChartProps {
  data: any[];
  columns: string[];
}

export const DynamicChart: React.FC<DynamicChartProps> = ({ data, columns }) => {
  if (!data || data.length === 0 || columns.length < 2) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500 italic">
        Result set too small to chart (need at least 2 columns).
      </div>
    );
  }

  // Auto-detect chart properties.
  // We assume the first column is the X-Axis (category) and the remaining are numerical data series.
  const xAxisKey = columns[0];
  const seriesKeys = columns.slice(1);

  // If there are many data points or it contains dates, a LineChart might be better, 
  // but we default to BarChart for simple aggregated queries.
  const isTimeSeries = xAxisKey.toLowerCase().includes('date') || xAxisKey.toLowerCase().includes('time');

  return (
    <div className="h-96 w-full">
      <ResponsiveContainer width="100%" height="100%">
        {isTimeSeries ? (
          <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey={xAxisKey} stroke="currentColor" />
            <YAxis stroke="currentColor" />
            <Tooltip 
              contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }} 
            />
            {seriesKeys.map((key, i) => (
              <Line key={key} type="monotone" dataKey={key} stroke={`hsl(var(--primary))`} strokeWidth={3} />
            ))}
          </LineChart>
        ) : (
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey={xAxisKey} stroke="currentColor" />
            <YAxis stroke="currentColor" />
            <Tooltip 
              contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }}
              cursor={{ fill: 'hsl(var(--primary) / 0.1)' }}
            />
            {seriesKeys.map((key) => (
              <Bar key={key} dataKey={key} fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
};
