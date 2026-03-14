'use client';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatCurrency, formatScore } from '@/lib/formatters';
import type { Position } from '@/types/api';

interface HoldingsTableProps {
  positions: Position[];
}

export function HoldingsTable({ positions }: HoldingsTableProps) {
  if (positions.length === 0) {
    return <p className="py-8 text-center text-muted-foreground">No open positions</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Ticker</TableHead>
          <TableHead className="text-right">Qty</TableHead>
          <TableHead className="text-right">Price</TableHead>
          <TableHead className="text-right">P&amp;L</TableHead>
          <TableHead className="text-right">Stop</TableHead>
          <TableHead className="text-right">Target</TableHead>
          <TableHead className="text-right">Score</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {positions.map((pos) => (
          <TableRow key={pos.symbol}>
            <TableCell className="font-medium">{pos.symbol}</TableCell>
            <TableCell className="text-right font-mono tabular-nums">{pos.qty}</TableCell>
            <TableCell className="text-right font-mono tabular-nums">
              {formatCurrency(pos.current_price)}
            </TableCell>
            <TableCell
              className={`text-right font-mono tabular-nums ${pos.pnl_dollar >= 0 ? 'text-profit' : 'text-loss'}`}
            >
              {formatCurrency(pos.pnl_dollar)}
            </TableCell>
            <TableCell className="text-right font-mono tabular-nums">
              {formatCurrency(pos.stop_price)}
            </TableCell>
            <TableCell className="text-right font-mono tabular-nums">
              {formatCurrency(pos.target_price)}
            </TableCell>
            <TableCell className="text-right font-mono tabular-nums">
              {formatScore(pos.composite_score)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
