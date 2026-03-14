'use client';

import type { ColumnDef } from '@tanstack/react-table';
import { ArrowUpDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatScore } from '@/lib/formatters';
import type { ScoreRow } from '@/types/api';

function signalVariant(signal: string) {
  switch (signal) {
    case 'BUY':
      return 'default' as const;
    case 'SELL':
      return 'destructive' as const;
    default:
      return 'secondary' as const;
  }
}

export const scoringColumns: ColumnDef<ScoreRow>[] = [
  {
    accessorKey: 'symbol',
    header: 'Symbol',
    cell: ({ row }) => <span className="font-medium">{row.getValue('symbol')}</span>,
  },
  {
    accessorKey: 'composite',
    header: ({ column }) => (
      <Button
        variant="ghost"
        className="px-0"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        Composite
        <ArrowUpDown className="ml-1 size-3.5" />
      </Button>
    ),
    cell: ({ row }) => (
      <span className="font-mono tabular-nums">{formatScore(row.getValue('composite'))}</span>
    ),
  },
  {
    accessorKey: 'risk_adjusted',
    header: ({ column }) => (
      <Button
        variant="ghost"
        className="px-0"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        Risk-Adj
        <ArrowUpDown className="ml-1 size-3.5" />
      </Button>
    ),
    cell: ({ row }) => (
      <span className="font-mono tabular-nums">{formatScore(row.getValue('risk_adjusted'))}</span>
    ),
  },
  {
    accessorKey: 'strategy',
    header: 'Strategy',
    cell: ({ row }) => row.getValue('strategy'),
  },
  {
    accessorKey: 'signal',
    header: 'Signal',
    cell: ({ row }) => {
      const signal = row.getValue('signal') as string;
      return <Badge variant={signalVariant(signal)}>{signal}</Badge>;
    },
  },
];
