import { NextResponse } from 'next/server';
import { backendGet } from '../_lib';

export const dynamic = 'force-dynamic';

export async function GET() {
  const regime = await backendGet<{ regime: string; confidence: number }>(
    '/api/v1/regime/current'
  );

  return NextResponse.json({
    total_value: 0,
    today_pnl: 0,
    drawdown_pct: 0,
    last_pipeline: null,
    positions: [],
    trade_history: [],
    equity_curve: { dates: [], values: [] },
    regime_periods: regime
      ? [{ start: new Date().toISOString(), end: new Date().toISOString(), regime: regime.regime }]
      : [],
  });
}
