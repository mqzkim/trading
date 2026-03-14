'use client';

import { Progress, ProgressLabel } from '@/components/ui/progress';

export function PositionLimits({ count, max }: { count: number; max: number }) {
  const pct = max > 0 ? (count / max) * 100 : 0;
  const isNearLimit = count / max > 0.8;

  return (
    <Progress value={pct} className="w-full">
      <ProgressLabel>Position Limits</ProgressLabel>
      <span
        className={`ml-auto text-sm tabular-nums ${isNearLimit ? 'text-interactive' : 'text-muted-foreground'}`}
      >
        {count} / {max}
      </span>
    </Progress>
  );
}
