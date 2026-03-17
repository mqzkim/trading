'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { usePerformance } from '@/hooks/use-performance';
import type { BrinsonFachlerRow, ProposalItem, ApprovalHistoryItem } from '@/types/api';

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

function pct(v: number) {
  return `${(v * 100).toFixed(2)}%`;
}

function BrinsonTable({ rows }: { rows: BrinsonFachlerRow[] }) {
  if (rows.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No performance data yet — generates after first closed trades
      </p>
    );
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Level</TableHead>
          <TableHead className="text-right">Allocation Effect</TableHead>
          <TableHead className="text-right">Selection Effect</TableHead>
          <TableHead className="text-right">Interaction Effect</TableHead>
          <TableHead className="text-right">Total Effect</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.name}>
            <TableCell className="font-medium">{row.name}</TableCell>
            <TableCell className="text-right font-mono">{pct(row.allocation_effect)}</TableCell>
            <TableCell className="text-right font-mono">{pct(row.selection_effect)}</TableCell>
            <TableCell className="text-right font-mono">{pct(row.interaction_effect)}</TableCell>
            <TableCell className="text-right font-mono">{pct(row.total_effect)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function ICBadge({ value, threshold }: { value: number | null; threshold: number }) {
  if (value === null) {
    return <span className="font-mono text-muted-foreground">--</span>;
  }
  const pass = value >= threshold;
  return (
    <span className={`font-mono ${pass ? 'text-green-400' : 'text-red-400'}`}>
      {value.toFixed(4)}
    </span>
  );
}

function KellyBadge({ value }: { value: number | null }) {
  if (value === null) {
    return <span className="font-mono text-muted-foreground">--</span>;
  }
  const color =
    value >= 70 ? 'text-green-400' : value >= 50 ? 'text-yellow-400' : 'text-red-400';
  return <span className={`font-mono ${color}`}>{value.toFixed(1)}%</span>;
}

function ProposalRow({
  proposal,
  onApprove,
  onReject,
  isPending,
}: {
  proposal: ProposalItem;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  isPending: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded border border-border p-3">
      <div className="space-y-0.5">
        <p className="text-sm font-medium">
          {proposal.regime} — {proposal.axis}:{' '}
          <span className="font-mono">
            {(proposal.current_weight * 100).toFixed(0)}% →{' '}
            {(proposal.proposed_weight * 100).toFixed(0)}%
          </span>
        </p>
        <p className="text-xs text-muted-foreground">
          Walk-forward Sharpe: {proposal.walk_forward_sharpe.toFixed(2)}
        </p>
      </div>
      <div className="flex gap-2">
        <Button
          size="sm"
          variant="default"
          disabled={isPending}
          onClick={() => onApprove(proposal.id)}
        >
          Approve
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={isPending}
          onClick={() => onReject(proposal.id)}
        >
          Reject
        </Button>
      </div>
    </div>
  );
}

function ApprovalHistoryTable({ rows }: { rows: ApprovalHistoryItem[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-muted-foreground">No approval history yet</p>;
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Date</TableHead>
          <TableHead>Regime</TableHead>
          <TableHead>Axis</TableHead>
          <TableHead>Change</TableHead>
          <TableHead>Decision</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((item) => (
          <TableRow key={item.id}>
            <TableCell className="font-mono text-xs">
              {item.decided_at ? item.decided_at.slice(0, 10) : '--'}
            </TableCell>
            <TableCell>{item.regime}</TableCell>
            <TableCell>{item.axis}</TableCell>
            <TableCell className="font-mono">
              {(item.current_weight * 100).toFixed(0)}% →{' '}
              {(item.proposed_weight * 100).toFixed(0)}%
            </TableCell>
            <TableCell>
              <span
                className={
                  item.status === 'approved' ? 'text-green-400' : 'text-red-400'
                }
              >
                {item.status === 'approved' ? 'Approved' : 'Rejected'}
              </span>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export default function PerformancePage() {
  const { data, isLoading, approveProposal, rejectProposal } = usePerformance();

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
  const brinsonRows = data?.brinson_table ?? [];
  const icPerAxis = data?.signal_ic_per_axis ?? null;
  const proposals = data?.proposals ?? [];
  const approvalHistory = data?.approval_history ?? [];
  const tradeCount = data?.trade_count ?? 0;
  const mutationPending = approveProposal.isPending || rejectProposal.isPending;

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
          <BrinsonTable rows={brinsonRows} />
        </CardContent>
      </Card>

      {/* Equity Curve placeholder (reserved for chart) */}
      <Card>
        <CardHeader>
          <CardTitle>Equity Curve</CardTitle>
        </CardHeader>
        <CardContent className="h-64 flex items-center justify-center">
          <p className="text-sm text-muted-foreground">
            {tradeCount > 0
              ? 'Equity curve chart will render here'
              : 'No performance data yet — generates after first closed trades'}
          </p>
        </CardContent>
      </Card>

      {/* Strategy Scorecard */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Scorecard</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-6 lg:grid-cols-4">
            <div>
              <p className="text-sm text-muted-foreground">Fundamental IC</p>
              <p className="text-lg">
                <ICBadge value={icPerAxis?.fundamental ?? null} threshold={0.03} />
              </p>
              <p className="text-xs text-muted-foreground">threshold: 0.03</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Technical IC</p>
              <p className="text-lg">
                <ICBadge value={icPerAxis?.technical ?? null} threshold={0.03} />
              </p>
              <p className="text-xs text-muted-foreground">threshold: 0.03</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Sentiment IC</p>
              <p className="text-lg">
                <ICBadge value={icPerAxis?.sentiment ?? null} threshold={0.03} />
              </p>
              <p className="text-xs text-muted-foreground">threshold: 0.03</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Kelly Efficiency</p>
              <p className="text-lg">
                <KellyBadge value={data?.kelly_efficiency ?? null} />
              </p>
              <p className="text-xs text-muted-foreground">threshold: 70%</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Parameter Proposals — hidden when < 50 trades */}
      {tradeCount >= 50 && (
        <Card>
          <CardHeader>
            <CardTitle>Parameter Proposals</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {mutationPending && (
              <p className="text-sm text-muted-foreground">Processing...</p>
            )}

            {/* Pending proposals */}
            <div className="space-y-2">
              {proposals.filter((p) => p.status === 'pending').length === 0 ? (
                <p className="text-sm text-muted-foreground">No pending proposals</p>
              ) : (
                proposals
                  .filter((p) => p.status === 'pending')
                  .map((proposal) => (
                    <ProposalRow
                      key={proposal.id}
                      proposal={proposal}
                      onApprove={(id) => approveProposal.mutate(id)}
                      onReject={(id) => rejectProposal.mutate(id)}
                      isPending={mutationPending}
                    />
                  ))
              )}
            </div>

            {/* Approval History */}
            <div>
              <h3 className="text-sm font-semibold mb-2">Approval History</h3>
              <ApprovalHistoryTable rows={approvalHistory.slice(0, 5)} />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
