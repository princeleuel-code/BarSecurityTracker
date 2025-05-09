import { ArrowDownIcon, ArrowUpIcon } from 'lucide-react';
import { Card, CardContent } from './card';
import { cn } from '@/lib/utils';

interface MetricProps {
  label: string;
  value: string | number;
  trend?: number;
  unit?: string;
  className?: string;
}

export function Metric({ label, value, trend, unit, className }: MetricProps) {
  return (
    <Card className={className}>
      <CardContent className="p-4">
        <div className="flex justify-between">
          <p className="text-sm font-medium text-muted-foreground">
            {label}
          </p>
          {typeof trend === 'number' && (
            <div 
              className={cn(
                "flex items-center gap-1 text-xs",
                trend > 0 ? "text-green-500" : "text-red-500"
              )}
            >
              {trend > 0 ? (
                <ArrowUpIcon className="h-3 w-3" />
              ) : (
                <ArrowDownIcon className="h-3 w-3" />
              )}
              <span>{Math.abs(trend).toFixed(1)}%</span>
            </div>
          )}
        </div>
        <div className="mt-2 flex items-baseline">
          <h3 className="text-2xl font-semibold">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </h3>
          {unit && (
            <span className="ml-1 text-sm text-muted-foreground">
              {unit}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}