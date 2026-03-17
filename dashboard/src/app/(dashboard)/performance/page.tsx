'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { usePerformance } from '@/hooks/use-performance';

function KPICard({ label, value, unit }: { label: string; value: number | null; unit?: string }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-2xl font-bold font-mono tabular-nums">
          {value !== null ? `${value.toFixed(2)}${unit ?? ''}` : '--'}
        </p>
      </CardContent>
    </Card>
  );
}

export default function PerformancePage() {
  const { data, isLoading } = usePerformance();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const kpis = data?.kpis;
  const hasData = data && data.trade_count > 0;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Performance Attribution</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KPICard label="Sharpe Ratio" value={kpis?.sharpe ?? null} />
        <KPICard label="Sortino Ratio" value={kpis?.sortino ?? null} />
        <KPICard label="Win Rate" value={kpis?.win_rate ?? null} unit="%" />
        <KPICard label="Max Drawdown" value={kpis?.max_drawdown ?? null} unit="%" />
      </div>

      {/* Brinson-Fachler Decomposition */}
      <Card>
        <CardHeader>
          <CardTitle>Brinson-Fachler Attribution</CardTitle>
        </CardHeader>
        <CardContent>
          {hasData ? (
            <p className="text-sm text-muted-foreground">Brinson-Fachler table will render here</p>
          ) : (
            <p className="text-sm text-muted-foreground">
              No performance data yet — generates after first closed trades
            </p>
          )}
        </CardContent>
      </Card>

      {/* Equity Curve */}
      <Card>
        <CardHeader>
          <CardTitle>Equity Curve</CardTitle>
        </CardHeader>
        <CardContent className="h-64 flex items-center justify-center">
          {hasData ? (
            <p className="text-sm text-muted-foreground">Equity curve chart will render here</p>
          ) : (
            <p className="text-sm text-muted-foreground">
              No performance data yet — generates after first closed trades
            </p>
          )}
        </CardContent>
      </Card>

      {/* Strategy Scorecard */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Scorecard</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-muted-foreground">Signal IC (threshold: 0.03)</p>
              <p className="text-lg font-mono tabular-nums">
                {data?.signal_ic !== null ? data?.signal_ic?.toFixed(4) : '--'}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Kelly Efficiency (threshold: 70%)</p>
              <p className="text-lg font-mono tabular-nums">
                {data?.kelly_efficiency !== null ? `${data?.kelly_efficiency?.toFixed(1)}%` : '--'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
