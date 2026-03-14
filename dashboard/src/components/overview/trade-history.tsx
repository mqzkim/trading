'use client';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatCurrency, formatDate, formatScore } from '@/lib/formatters';
import type { TradeHistoryItem } from '@/types/api';

interface TradeHistoryProps {
  trades: TradeHistoryItem[];
}

function directionColor(direction: string): string {
  const d = direction.toUpperCase();
  if (d === 'BUY' || d === 'LONG') return 'text-profit';
  if (d === 'SELL' || d === 'SHORT') return 'text-loss';
  return '';
}

export function TradeHistory({ trades }: TradeHistoryProps) {
  if (trades.length === 0) {
    return <p className="py-8 text-center text-muted-foreground">No executed trades</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Symbol</TableHead>
          <TableHead>Direction</TableHead>
          <TableHead className="text-right">Entry</TableHead>
          <TableHead className="text-right">Stop</TableHead>
          <TableHead className="text-right">Target</TableHead>
          <TableHead className="text-right">Qty</TableHead>
          <TableHead className="text-right">Value</TableHead>
          <TableHead className="text-right">Score</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Date</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {trades.map((trade) => (
          <TableRow
            key={`${trade.symbol}-${trade.created_at}-${trade.direction}-${trade.entry_price}`}
          >
            <TableCell className="font-medium">{trade.symbol}</TableCell>
            <TableCell className={directionColor(trade.direction)}>{trade.direction}</TableCell>
            <TableCell className="text-right font-mono tabular-nums">
              {formatCurrency(trade.entry_price)}
            </TableCell>
            <TableCell className="text-right font-mono tabular-nums">
              {formatCurrency(trade.stop_loss_price)}
            </TableCell>
            <TableCell className="text-right font-mono tabular-nums">
              {formatCurrency(trade.take_profit_price)}
            </TableCell>
            <TableCell className="text-right font-mono tabular-nums">{trade.quantity}</TableCell>
            <TableCell className="text-right font-mono tabular-nums">
              {formatCurrency(trade.position_value)}
            </TableCell>
            <TableCell className="text-right font-mono tabular-nums">
              {formatScore(trade.composite_score)}
            </TableCell>
            <TableCell>{trade.status}</TableCell>
            <TableCell>{formatDate(trade.created_at)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
