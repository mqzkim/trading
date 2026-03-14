'use client';

import { EquityCurve } from '@/components/overview/equity-curve';
import { HoldingsTable } from '@/components/overview/holdings-table';
import { KpiCards } from '@/components/overview/kpi-cards';
import { TradeHistory } from '@/components/overview/trade-history';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useOverview } from '@/hooks/use-overview';

export default function OverviewPage() {
  const { data, isLoading, error } = useOverview();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-40" />
        <div className="grid grid-cols-4 gap-4">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
        <Skeleton className="h-64" />
        <Skeleton className="h-48" />
      </div>
    );
  }

  if (error) {
    return <div className="p-8 text-destructive">Backend connection failed: {error.message}</div>;
  }

  if (!data) return null;

  const equityCurveData = data.equity_curve.dates.map((date, i) => ({
    time: date,
    value: data.equity_curve.values[i],
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold mb-4">Overview</h1>

      <KpiCards data={data} />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Holdings</CardTitle>
          </CardHeader>
          <CardContent>
            <HoldingsTable positions={data.positions} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Trades</CardTitle>
          </CardHeader>
          <CardContent>
            <TradeHistory trades={data.trade_history} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Equity Curve</CardTitle>
        </CardHeader>
        <CardContent>
          <EquityCurve data={equityCurveData} regimePeriods={data.regime_periods} />
        </CardContent>
      </Card>
    </div>
  );
}
