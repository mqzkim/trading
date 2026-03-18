import { proxyPost } from '../../_proxy';

export async function POST() {
  return proxyPost('/api/v1/approval/resume', {});
}
