import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { PipelineData } from '@/types/api';

export function usePipeline() {
  return useQuery<PipelineData>({
    queryKey: ['pipeline'],
    queryFn: async () => {
      const res = await fetch('/api/v1/dashboard/pipeline');
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    staleTime: 30_000,
    retry: 1,
  });
}

export function usePipelineRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { symbols: string[]; dry_run: boolean }) => {
      const res = await fetch('/api/v1/dashboard/pipeline/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline'] });
    },
  });
}

export function useApprovalCreate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      score_threshold: number;
      allowed_regimes: string[];
      max_per_trade_pct: number;
      daily_budget_cap: number;
      expires_at: string;
    }) => {
      const res = await fetch('/api/v1/dashboard/approval/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline'] });
    },
  });
}

export function useApprovalSuspend() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { approval_id?: string }) => {
      const res = await fetch('/api/v1/dashboard/approval/suspend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline'] });
    },
  });
}

export function useApprovalResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { approval_id?: string }) => {
      const res = await fetch('/api/v1/dashboard/approval/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline'] });
    },
  });
}

export function useReviewAction(action: 'approve' | 'reject') {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { review_id: number }) => {
      const res = await fetch(`/api/v1/dashboard/review/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline'] });
    },
  });
}
