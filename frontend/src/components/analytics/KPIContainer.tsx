import React from 'react';
import { Activity, DollarSign, Users, ShoppingCart } from 'lucide-react';

interface KPIContainerProps {
  data: any[];
  columns: string[];
}

export const KPIContainer: React.FC<KPIContainerProps> = ({ data, columns }) => {
  // Try to find a single aggregation metric if the query returned exactly one row
  if (!data || data.length !== 1) return null;
  
  const row = data[0];
  
  // Render a KPI card for each column
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {columns.map((col, index) => {
        const value = row[col];
        // Pick an icon based on column name heuristics
        let Icon = Activity;
        if (col.toLowerCase().includes('revenue') || col.toLowerCase().includes('sales')) Icon = DollarSign;
        if (col.toLowerCase().includes('user') || col.toLowerCase().includes('customer')) Icon = Users;
        if (col.toLowerCase().includes('unit')) Icon = ShoppingCart;

        return (
          <div key={col} className="glass-card rounded-2xl p-6 relative overflow-hidden group">
            <div className="absolute -right-4 -top-4 w-24 h-24 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-all"></div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-[hsl(var(--foreground))]/60 uppercase tracking-wider">{col.replace(/_/g, ' ')}</h3>
              <div className="p-2 bg-primary/10 rounded-lg text-primary">
                <Icon size={20} />
              </div>
            </div>
            <p className="text-3xl font-bold">
              {typeof value === 'number' && col.toLowerCase().includes('revenue') 
                ? `$${value.toLocaleString()}`
                : typeof value === 'number' 
                ? value.toLocaleString()
                : value}
            </p>
          </div>
        );
      })}
    </div>
  );
};
