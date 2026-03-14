'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { SignalItem } from '@/types/api';

function directionVariant(direction: string) {
  switch (direction) {
    case 'BUY':
      return 'default' as const;
    case 'SELL':
      return 'destructive' as const;
    default:
      return 'secondary' as const;
  }
}

function strengthColor(direction: string) {
  switch (direction) {
    case 'BUY':
      return 'bg-primary';
    case 'SELL':
      return 'bg-destructive';
    default:
      return 'bg-muted-foreground';
  }
}

export function SignalCards({ items }: { items: SignalItem[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">No active signals</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((item) => (
        <Card key={item.symbol}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">{item.symbol}</CardTitle>
              <Badge variant={directionVariant(item.direction)}>{item.direction}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm tabular-nums">
                {(item.strength * 100).toFixed(0)}%
              </span>
              <div
                className="relative h-2 flex-1 overflow-hidden rounded-full bg-muted"
                aria-hidden="true"
              >
                <div
                  className={`absolute inset-y-0 left-0 rounded-full ${strengthColor(item.direction)}`}
                  style={{ width: `${Math.min(item.strength * 100, 100)}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
