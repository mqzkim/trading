/**
 * Shared proxy helpers for dashboard BFF -> FastAPI backend.
 *
 * All internal calls use DASHBOARD_SECRET as Bearer token.
 */

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';
const SECRET = process.env.DASHBOARD_SECRET ?? 'dashboard-internal';
const TIMEOUT_MS = 10000;

export async function proxyGet(backendPath: string): Promise<Response> {
  try {
    const res = await fetch(`${BACKEND}${backendPath}`, {
      headers: {
        Authorization: `Bearer ${SECRET}`,
        Accept: 'application/json',
      },
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: 'no-store',
    });
    const data = await res.json();
    return Response.json(data, { status: res.status });
  } catch {
    return Response.json(
      { error: 'Backend unavailable' },
      { status: 503 },
    );
  }
}

export async function proxyPost(
  backendPath: string,
  body: unknown,
): Promise<Response> {
  try {
    const res = await fetch(`${BACKEND}${backendPath}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${SECRET}`,
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: 'no-store',
    });
    const data = await res.json();
    return Response.json(data, { status: res.status });
  } catch {
    return Response.json(
      { error: 'Backend unavailable' },
      { status: 503 },
    );
  }
}
