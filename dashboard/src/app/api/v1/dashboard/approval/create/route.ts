import { NextRequest } from 'next/server';
import { proxyPost } from '../../_proxy';

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  return proxyPost('/api/v1/approval/create', body);
}
