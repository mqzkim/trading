'use client';

import { DrawdownGauge } from '@/components/risk/drawdown-gauge';
import { PositionLimits } from '@/components/risk/position-limits';
import { RegimeBadge } from '@/components/risk/regime-badge';
import { RegimeProbabilities } from '@/components/risk/regime-probabilities';
import { SectorDonut } from '@/components/risk/sector-donut';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useRisk } from '@/hooks/use-risk';

export default function RiskPage() {
  const { data, isLoading, error } = useRisk();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-40" />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Skeleton className="h-24" />
          <Skeleton className="h-8" />
        </div>
      </div>
    );
  }

  if (error) {
    return <div className="p-8 text-destructive">Backend connection failed: {error.message}</div>;
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Risk</h1>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Drawdown</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-center">
            <DrawdownGauge pct={data.drawdown_pct} level={data.drawdown_level} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sector Exposure</CardTitle>
          </CardHeader>
          <CardContent>
            <SectorDonut sectors={data.sector_weights} />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Position Limits</CardTitle>
          </CardHeader>
          <CardContent>
            <PositionLimits count={data.position_count} max={data.max_positions} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Market Regime</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <RegimeBadge regime={data.regime} />
            {data.regime_probabilities && Object.keys(data.regime_probabilities).length > 0 && (
              <div className="mt-3">
                <RegimeProbabilities
                  probabilities={data.regime_probabilities}
                  dominant={data.regime}
                />
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              Current market regime detected by HMM model
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
