import { NextResponse } from 'next/server';

export async function POST() {
  return NextResponse.json({ status: 'queued', run_id: null }, { status: 202 });
}
