'use client';

import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

const REGIME_COLORS: Record<string, string> = {
  Bull: 'text-green-400',
  Bear: 'text-red-400',
  Sideways: 'text-yellow-400',
  Crisis: 'text-orange-400',
};

interface RegimeProbabilitiesProps {
  probabilities: Record<string, number>;
  dominant: string;
}

export function RegimeProbabilities({ probabilities, dominant }: RegimeProbabilitiesProps) {
  if (!probabilities || Object.keys(probabilities).length === 0) {
    return <p className="text-sm text-muted-foreground">No regime data available</p>;
  }

  return (
    <div className="space-y-2">
      {Object.entries(probabilities).map(([regime, prob]) => (
        <div
          key={regime}
          className={cn(
            'flex items-center gap-3 rounded-md p-1.5',
            regime === dominant && 'ring-1 ring-primary font-bold',
          )}
        >
          <span className={cn('w-20 text-sm', REGIME_COLORS[regime] ?? 'text-foreground')}>
            {regime}
          </span>
          <Progress value={prob * 100} className="flex-1" />
          <span className="w-12 text-right text-sm font-mono tabular-nums">
            {Math.round(prob * 100)}%
          </span>
        </div>
      ))}
    </div>
  );
}
