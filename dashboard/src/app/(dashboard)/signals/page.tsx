'use client';

import { scoringColumns } from '@/components/signals/columns';
import { ScoreBreakdownPanel } from '@/components/signals/score-breakdown-panel';
import { SignalCards } from '@/components/signals/signal-cards';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DataTable } from '@/components/ui/data-table';
import { Skeleton } from '@/components/ui/skeleton';
import { useSignals } from '@/hooks/use-signals';

export default function SignalsPage() {
  const { data, isLoading, error } = useSignals();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-64" />
        <Skeleton className="h-48" />
      </div>
    );
  }

  if (error) {
    return <div className="p-8 text-destructive">Backend connection failed: {error.message}</div>;
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Signals</h1>

      <Card>
        <CardHeader>
          <CardTitle>Scoring Table</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={scoringColumns}
            data={data.scores}
            renderSubComponent={({ row }) => <ScoreBreakdownPanel scores={row.original} />}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Signal Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <SignalCards items={data.signals} />
        </CardContent>
      </Card>
    </div>
  );
}
