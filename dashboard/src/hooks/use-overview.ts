import { useQuery } from '@tanstack/react-query';
import type { OverviewData } from '@/types/api';

export function useOverview() {
  return useQuery<OverviewData>({
    queryKey: ['overview'],
    queryFn: async () => {
      const res = await fetch('/api/v1/dashboard/overview');
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    staleTime: 30_000,
    retry: 1,
  });
}
