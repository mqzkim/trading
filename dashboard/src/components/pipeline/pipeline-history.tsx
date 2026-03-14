'use client';

import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatDate } from '@/lib/formatters';
import type { PipelineRun } from '@/types/api';

const statusVariant: Record<string, 'default' | 'secondary' | 'destructive'> = {
  completed: 'secondary',
  running: 'default',
  failed: 'destructive',
};

export function PipelineHistory({
  runs,
  nextScheduled,
}: {
  runs: PipelineRun[];
  nextScheduled: string;
}) {
  if (runs.length === 0) {
    return (
      <div className="space-y-2">
        <p className="text-muted-foreground text-sm">No pipeline runs yet</p>
        <p className="text-muted-foreground text-xs">Next scheduled: {nextScheduled || '--'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Run ID</TableHead>
            <TableHead>Started</TableHead>
            <TableHead>Completed</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {runs.map((run) => (
            <TableRow key={run.run_id}>
              <TableCell className="font-mono text-xs">{run.run_id.slice(0, 8)}</TableCell>
              <TableCell>{formatDate(run.started_at)}</TableCell>
              <TableCell>{run.completed_at ? formatDate(run.completed_at) : '--'}</TableCell>
              <TableCell>
                <Badge variant={statusVariant[run.status] ?? 'secondary'}>{run.status}</Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <p className="text-muted-foreground text-xs">Next scheduled: {nextScheduled || '--'}</p>
    </div>
  );
}
