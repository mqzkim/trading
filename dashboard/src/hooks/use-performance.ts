import { useQuery } from '@tanstack/react-query';
import type { PerformanceData } from '@/types/api';

export function usePerformance() {
  return useQuery<PerformanceData>({
    queryKey: ['performance'],
    queryFn: async () => {
      const res = await fetch('/api/v1/dashboard/performance');
      if (!res.ok) {
        // Expected 404 until Phase 29 creates the endpoint
        return {
          kpis: null,
          brinson_table: null,
          equity_curve: null,
          signal_ic: null,
          kelly_efficiency: null,
          trade_count: 0,
        };
      }
      return res.json();
    },
    staleTime: 60_000,
    retry: false,
  });
}
