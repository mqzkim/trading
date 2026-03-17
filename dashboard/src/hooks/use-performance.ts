import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { PerformanceData } from '@/types/api';

const EMPTY_PERFORMANCE: PerformanceData = {
  kpis: null,
  brinson_table: null,
  equity_curve: null,
  signal_ic: null,
  kelly_efficiency: null,
  trade_count: 0,
  signal_ic_per_axis: null,
  proposals: null,
  approval_history: null,
};

export function usePerformance() {
  const queryClient = useQueryClient();

  const query = useQuery<PerformanceData>({
    queryKey: ['performance'],
    queryFn: async () => {
      const res = await fetch('/api/v1/dashboard/performance');
      if (!res.ok) {
        return EMPTY_PERFORMANCE;
      }
      return res.json();
    },
    staleTime: 60_000,
    retry: false,
  });

  const approveProposal = useMutation({
    mutationFn: async (proposalId: string) => {
      const res = await fetch(
        `/api/v1/dashboard/performance/proposals/${proposalId}/approve`,
        { method: 'PUT' },
      );
      if (!res.ok) throw new Error('Approve failed');
      return res.json();
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['performance'] }),
  });

  const rejectProposal = useMutation({
    mutationFn: async (proposalId: string) => {
      const res = await fetch(
        `/api/v1/dashboard/performance/proposals/${proposalId}/reject`,
        { method: 'PUT' },
      );
      if (!res.ok) throw new Error('Reject failed');
      return res.json();
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['performance'] }),
  });

  return { ...query, approveProposal, rejectProposal };
}
