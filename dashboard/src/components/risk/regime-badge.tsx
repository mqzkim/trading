'use client';

import { Badge } from '@/components/ui/badge';

const REGIME_STYLES: Record<string, string> = {
  bull: 'bg-profit/20 text-profit border-profit/30',
  bear: 'bg-loss/20 text-loss border-loss/30',
  accumulation: 'bg-chart-1/20 text-chart-1 border-chart-1/30',
  distribution: 'bg-interactive/20 text-interactive border-interactive/30',
};

const DEFAULT_STYLE = 'bg-muted text-muted-foreground';

export function RegimeBadge({ regime }: { regime: string }) {
  const key = regime.toLowerCase();
  const style = REGIME_STYLES[key] ?? DEFAULT_STYLE;

  return (
    <Badge variant="outline" className={style}>
      {regime}
    </Badge>
  );
}
