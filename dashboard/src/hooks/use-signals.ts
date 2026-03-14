import { useQuery } from '@tanstack/react-query';
import type { SignalsData } from '@/types/api';

export function useSignals() {
  return useQuery<SignalsData>({
    queryKey: ['signals'],
    queryFn: async () => {
      const res = await fetch('/api/v1/dashboard/signals');
      if (!res.ok) throw new Error(`Backend error: ${res.status}`);
      return res.json();
    },
    staleTime: 30_000,
    retry: 1,
  });
}
