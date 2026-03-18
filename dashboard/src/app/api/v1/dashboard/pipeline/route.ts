import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
  return NextResponse.json({
    pipeline_runs: [],
    next_scheduled: null,
    approval_status: null,
    daily_budget: { spent: 0, limit: 0, remaining: 0 },
    review_queue: [],
  });
}
