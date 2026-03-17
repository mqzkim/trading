import { NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

const EMPTY_RESPONSE = {
  trade_count: 0,
  kpis: null,
  brinson_table: null,
  equity_curve: null,
  signal_ic: null,
  kelly_efficiency: null,
  signal_ic_per_axis: null,
  proposals: null,
  approval_history: null,
};

export async function GET() {
  try {
    const token = process.env.API_JWT_TOKEN ?? '';
    const res = await fetch(`${API_BASE}/api/v1/performance/attribution`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: 'no-store',
    });
    if (!res.ok) {
      return NextResponse.json(EMPTY_RESPONSE, { status: 200 });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(EMPTY_RESPONSE);
  }
}
