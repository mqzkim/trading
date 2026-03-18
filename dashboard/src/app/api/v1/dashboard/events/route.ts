// SSE proxy: forwards events from FastAPI backend.
// Returns an empty stream when backend is unavailable (graceful degradation).

export const dynamic = 'force-dynamic';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';
const SECRET = process.env.DASHBOARD_SECRET ?? 'dashboard-internal';

export async function GET() {
  const encoder = new TextEncoder();

  // Try to proxy from FastAPI SSE endpoint
  try {
    const upstream = await fetch(`${BACKEND_URL}/api/v1/events`, {
      headers: {
        Accept: 'text/event-stream',
        Authorization: `Bearer ${SECRET}`,
      },
      signal: AbortSignal.timeout(3000),
    });

    if (upstream.ok && upstream.body) {
      return new Response(upstream.body, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
        },
      });
    }
  } catch {
    // Backend unavailable -- return empty keep-alive stream
  }

  // Graceful fallback: empty SSE stream (no events, no error)
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(': connected\n\n'));
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}
