import { NextRequest } from 'next/server';
import { proxyPost } from '../../../_proxy';

export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  return proxyPost(`/api/v1/review/${id}/approve`, {});
}
