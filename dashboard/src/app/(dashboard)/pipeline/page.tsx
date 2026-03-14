'use client';
import { useEffect, useState } from 'react';

export default function PipelinePage() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/v1/dashboard/pipeline')
      .then((res) => {
        if (!res.ok) throw new Error(`Backend error: ${res.status}`);
        return res.json();
      })
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return (
      <div className="p-8 text-red-400">
        Backend connection failed - Start FastAPI first: {error}
      </div>
    );
  }
  if (!data) return <div className="p-8 text-gray-400">Loading...</div>;

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Pipeline</h1>
      <pre className="bg-gray-900 p-4 rounded text-sm overflow-auto text-gray-300">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}
