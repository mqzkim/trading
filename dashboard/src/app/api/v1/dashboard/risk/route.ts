import { NextResponse } from 'next/server';
import { backendGet } from '../_lib';

export const dynamic = 'force-dynamic';

interface RegimeResponse {
  regime: string;
  confidence: number;
  probabilities?: Record<string, number>;
}

export async function GET() {
  const regime = await backendGet<RegimeResponse>('/api/v1/regime/current');

  return NextResponse.json({
    drawdown_pct: 0,
    drawdown_level: 'normal',
    sector_weights: {},
    position_count: 0,
    max_positions: 10,
    regime: regime?.regime ?? 'unknown',
    regime_confidence: regime?.confidence ?? 0,
    regime_probabilities: regime?.probabilities ?? {},
  });
}
