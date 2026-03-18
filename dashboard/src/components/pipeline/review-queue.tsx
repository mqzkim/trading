'use client';

import { Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useReviewAction } from '@/hooks/use-pipeline';
import { formatDate, formatScore } from '@/lib/formatters';
import type { ReviewItem } from '@/types/api';

export function ReviewQueue({ items }: { items: ReviewItem[] | null | undefined }) {
  const approve = useReviewAction('approve');
  const reject = useReviewAction('reject');

  if (!items || items.length === 0) {
    return <p className="text-muted-foreground text-sm">No pending reviews</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Symbol</TableHead>
          <TableHead>Strategy</TableHead>
          <TableHead className="text-right">Score</TableHead>
          <TableHead>Reason</TableHead>
          <TableHead>Date</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <TableRow key={item.id}>
            <TableCell className="font-medium">{item.symbol}</TableCell>
            <TableCell>{item.strategy}</TableCell>
            <TableCell className="text-right font-mono tabular-nums">
              {formatScore(item.score)}
            </TableCell>
            <TableCell className="max-w-[200px] truncate">{item.reason ?? '--'}</TableCell>
            <TableCell>{formatDate(item.created_at)}</TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end gap-1">
                <Button
                  size="icon-xs"
                  variant="ghost"
                  disabled={approve.isPending}
                  onClick={() => approve.mutate({ review_id: item.id })}
                >
                  <Check className="text-profit" />
                </Button>
                <Button
                  size="icon-xs"
                  variant="ghost"
                  disabled={reject.isPending}
                  onClick={() => reject.mutate({ review_id: item.id })}
                >
                  <X className="text-loss" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
