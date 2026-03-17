'use client';

import { cn } from '@/lib/utils';
import type { ScoreRow } from '@/types/api';

function ScoreBar({ label, value }: { label: string; value: number | null }) {
  const displayValue = value ?? 0;
  const color =
    displayValue >= 70 ? 'bg-green-500' : displayValue >= 40 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2">
      <span className="w-24 text-xs text-muted-foreground">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-muted">
        <div
          className={cn('h-2 rounded-full', color)}
          style={{ width: `${Math.min(displayValue, 100)}%` }}
        />
      </div>
      <span className="w-10 text-right text-xs font-mono tabular-nums">
        {value !== null ? value.toFixed(0) : '--'}
      </span>
    </div>
  );
}

export function ScoreBreakdownPanel({ scores }: { scores: ScoreRow }) {
  const isSentimentUnavailable = scores.sentiment_confidence === 'NONE';

  return (
    <div className="grid grid-cols-1 gap-4 p-4 bg-muted/30 rounded-md lg:grid-cols-3">
      {/* Axis scores */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-muted-foreground">Axis Scores</h4>
        <div className="flex items-center gap-3 text-sm font-mono">
          <span>F: {scores.fundamental_score?.toFixed(0) ?? '--'}</span>
          <span>|</span>
          <span>T: {scores.technical_score?.toFixed(0) ?? '--'}</span>
          <span>|</span>
          <span className={cn(isSentimentUnavailable && 'text-muted-foreground/50')}>
            S: {scores.sentiment_score?.toFixed(0) ?? '--'}
          </span>
          {!isSentimentUnavailable && (
            <span className="text-xs text-muted-foreground">({scores.sentiment_confidence})</span>
          )}
        </div>
      </div>

      {/* Technical sub-scores placeholder */}
      <div className="space-y-1.5">
        <h4 className="text-xs font-semibold text-muted-foreground">Technical</h4>
        <ScoreBar label="RSI" value={null} />
        <ScoreBar label="MACD" value={null} />
        <ScoreBar label="MA" value={null} />
        <ScoreBar label="ADX" value={null} />
        <ScoreBar label="OBV" value={null} />
      </div>

      {/* Sentiment sub-scores */}
      <div className={cn('space-y-1.5', isSentimentUnavailable && 'opacity-40')}>
        <h4 className="text-xs font-semibold text-muted-foreground">
          Sentiment
          {isSentimentUnavailable && (
            <span className="ml-2 text-xs font-normal italic">Sentiment data unavailable</span>
          )}
        </h4>
        <ScoreBar label="News" value={null} />
        <ScoreBar label="Insider" value={null} />
        <ScoreBar label="Institutional" value={null} />
        <ScoreBar label="Analyst" value={null} />
      </div>
    </div>
  );
}
