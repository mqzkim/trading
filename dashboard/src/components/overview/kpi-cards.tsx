'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatCurrency, formatPercent } from '@/lib/formatters';
import type { OverviewData } from '@/types/api';

interface KpiCardsProps {
  data: OverviewData;
}

function drawdownColor(pct: number): string {
  if (pct <= 10) return 'text-profit';
  if (pct <= 15) return 'text-interactive';
  return 'text-loss';
}

export function KpiCards({ data }: KpiCardsProps) {
  const pnlPositive = data.today_pnl >= 0;

  return (
    <div className="grid grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-muted-foreground">Total Value</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-mono tabular-nums">{formatCurrency(data.total_value)}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-muted-foreground">Daily P&amp;L</CardTitle>
        </CardHeader>
        <CardContent>
          <p
            className={`text-2xl font-mono tabular-nums ${pnlPositive ? 'text-profit' : 'text-loss'}`}
          >
            {pnlPositive ? '+' : ''}
            {formatCurrency(data.today_pnl)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-muted-foreground">Drawdown</CardTitle>
        </CardHeader>
        <CardContent>
          <p className={`text-2xl font-mono tabular-nums ${drawdownColor(data.drawdown_pct)}`}>
            {formatPercent(data.drawdown_pct)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-muted-foreground">Pipeline</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-lg font-mono">{data.last_pipeline?.status ?? 'No runs'}</p>
        </CardContent>
      </Card>
    </div>
  );
}
