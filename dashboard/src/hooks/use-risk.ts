import { useQuery } from '@tanstack/react-query';
import type { RiskData } from '@/types/api';

export function useRisk() {
  return useQuery<RiskData>({
    queryKey: ['risk'],
    queryFn: async () => {
      const res = await fetch('/api/v1/dashboard/risk');
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    staleTime: 30_000,
    retry: 1,
  });
}
