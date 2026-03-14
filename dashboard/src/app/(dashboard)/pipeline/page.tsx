'use client';

import { ApprovalControls } from '@/components/pipeline/approval-controls';
import { PipelineHistory } from '@/components/pipeline/pipeline-history';
import { PipelineRunForm } from '@/components/pipeline/pipeline-run-form';
import { ReviewQueue } from '@/components/pipeline/review-queue';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { usePipeline } from '@/hooks/use-pipeline';

export default function PipelinePage() {
  const { data, isLoading, error } = usePipeline();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-40" />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
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

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Pipeline</h1>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Run Pipeline</CardTitle>
          </CardHeader>
          <CardContent>
            <PipelineRunForm />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Approval</CardTitle>
          </CardHeader>
          <CardContent>
            <ApprovalControls approval={data.approval_status} budget={data.daily_budget} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Pipeline History</CardTitle>
        </CardHeader>
        <CardContent>
          <PipelineHistory runs={data.pipeline_runs} nextScheduled={data.next_scheduled} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Trade Review Queue</CardTitle>
        </CardHeader>
        <CardContent>
          <ReviewQueue items={data.review_queue} />
        </CardContent>
      </Card>
    </div>
  );
}
