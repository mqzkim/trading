'use client';

import { type FormEvent, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { useApprovalCreate, useApprovalResume, useApprovalSuspend } from '@/hooks/use-pipeline';
import { formatCurrency } from '@/lib/formatters';
import type { ApprovalStatus, DailyBudget } from '@/types/api';

export function ApprovalControls({
  approval,
  budget,
}: {
  approval: ApprovalStatus | null;
  budget: DailyBudget;
}) {
  if (approval) {
    return <ApprovalStatusView approval={approval} budget={budget} />;
  }
  return <ApprovalCreateForm />;
}

function ApprovalCreateForm() {
  const [scoreThreshold, setScoreThreshold] = useState('70.0');
  const [allowedRegimes, setAllowedRegimes] = useState('Bull, Accumulation');
  const [maxPerTradePct, setMaxPerTradePct] = useState('8.0');
  const [dailyBudgetCap, setDailyBudgetCap] = useState('10000.0');
  const [expiresInDays, setExpiresInDays] = useState('30');
  const create = useApprovalCreate();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const regimes = allowedRegimes
      .split(',')
      .map((r) => r.trim())
      .filter(Boolean);
    create.mutate({
      score_threshold: Number.parseFloat(scoreThreshold),
      allowed_regimes: regimes,
      max_per_trade_pct: Number.parseFloat(maxPerTradePct),
      daily_budget_cap: Number.parseFloat(dailyBudgetCap),
      expires_in_days: Number.parseInt(expiresInDays, 10),
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label htmlFor="approval-score">Score Threshold</Label>
          <Input
            id="approval-score"
            type="number"
            step="0.1"
            value={scoreThreshold}
            onChange={(e) => setScoreThreshold(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="approval-max-pct">Max Per Trade %</Label>
          <Input
            id="approval-max-pct"
            type="number"
            step="0.1"
            value={maxPerTradePct}
            onChange={(e) => setMaxPerTradePct(e.target.value)}
          />
        </div>
      </div>

      <div className="space-y-1">
        <Label htmlFor="approval-regimes">Allowed Regimes</Label>
        <Input
          id="approval-regimes"
          placeholder="Bull, Accumulation"
          value={allowedRegimes}
          onChange={(e) => setAllowedRegimes(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label htmlFor="approval-budget">Daily Budget Cap</Label>
          <Input
            id="approval-budget"
            type="number"
            step="100"
            value={dailyBudgetCap}
            onChange={(e) => setDailyBudgetCap(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="approval-expires">Expires In (days)</Label>
          <Input
            id="approval-expires"
            type="number"
            value={expiresInDays}
            onChange={(e) => setExpiresInDays(e.target.value)}
          />
        </div>
      </div>

      <Button type="submit" disabled={create.isPending}>
        {create.isPending ? 'Creating...' : 'Create Approval'}
      </Button>
    </form>
  );
}

function ApprovalStatusView({
  approval,
  budget,
}: {
  approval: ApprovalStatus;
  budget: DailyBudget;
}) {
  const suspend = useApprovalSuspend();
  const resume = useApprovalResume();

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">Status</span>
        <Badge variant={approval.is_suspended ? 'destructive' : 'default'}>
          {approval.is_suspended ? 'Suspended' : 'Active'}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <span className="text-muted-foreground">Score Threshold</span>
        <span className="font-mono">{approval.score_threshold}</span>

        <span className="text-muted-foreground">Allowed Regimes</span>
        <span>{approval.allowed_regimes.join(', ')}</span>

        <span className="text-muted-foreground">Max Per Trade</span>
        <span className="font-mono">{approval.max_per_trade_pct}%</span>

        <span className="text-muted-foreground">Expires At</span>
        <span>{approval.expires_at.slice(0, 10)}</span>
      </div>

      <Separator />

      <div className="text-sm">
        <span className="text-muted-foreground">Daily Budget: </span>
        <span className="font-mono">
          {formatCurrency(budget.spent)} / {formatCurrency(budget.limit)}
        </span>
        <span className="text-muted-foreground"> (remaining: </span>
        <span className="font-mono">{formatCurrency(budget.remaining)}</span>
        <span className="text-muted-foreground">)</span>
      </div>

      <div className="flex gap-2">
        {!approval.is_suspended ? (
          <Button
            variant="destructive"
            disabled={suspend.isPending}
            onClick={() => suspend.mutate({ approval_id: approval.id })}
          >
            {suspend.isPending ? 'Suspending...' : 'Suspend'}
          </Button>
        ) : (
          <Button
            disabled={resume.isPending}
            onClick={() => resume.mutate({ approval_id: approval.id })}
          >
            {resume.isPending ? 'Resuming...' : 'Resume'}
          </Button>
        )}
      </div>
    </div>
  );
}
