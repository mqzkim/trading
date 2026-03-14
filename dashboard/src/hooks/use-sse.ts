import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

const EVENT_QUERY_MAP: Record<string, string[][]> = {
  OrderFilledEvent: [['overview']],
  DrawdownAlertEvent: [['risk'], ['overview']],
  RegimeChangedEvent: [['risk'], ['overview'], ['signals']],
  PipelineCompletedEvent: [['pipeline'], ['overview']],
  PipelineHaltedEvent: [['pipeline'], ['overview']],
};

export function useSSE() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const es = new EventSource('/api/v1/dashboard/events');

    for (const [eventType, queryKeys] of Object.entries(EVENT_QUERY_MAP)) {
      es.addEventListener(eventType, () => {
        for (const key of queryKeys) {
          queryClient.invalidateQueries({ queryKey: key });
        }
      });
    }

    return () => es.close();
  }, [queryClient]);
}
