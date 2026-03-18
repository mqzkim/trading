export const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000';
const TIMEOUT_MS = 5000;

export async function backendGet<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${BACKEND}${path}`, {
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!res.ok) return null;
    return res.json() as Promise<T>;
  } catch {
    return null;
  }
}
