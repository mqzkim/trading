import { proxyGet } from '../_proxy';

export const dynamic = 'force-dynamic';

export async function GET() {
  return proxyGet('/api/v1/review/queue');
}
