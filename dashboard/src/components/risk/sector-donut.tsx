'use client';

const SECTOR_COLORS = [
  'oklch(0.7 0.15 200)',
  'oklch(0.78 0.15 75)',
  'oklch(0.65 0.15 150)',
  'oklch(0.6 0.2 25)',
  'oklch(0.7 0.12 300)',
  'oklch(0.65 0.18 100)',
];

export function SectorDonut({ sectors }: { sectors: Record<string, number> }) {
  const entries = Object.entries(sectors);

  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No positions</p>;
  }

  let accumulated = 0;
  const stops: string[] = [];

  for (let i = 0; i < entries.length; i++) {
    const [, weight] = entries[i];
    const color = SECTOR_COLORS[i % SECTOR_COLORS.length];
    const start = accumulated;
    accumulated += weight;
    stops.push(`${color} ${start}% ${accumulated}%`);
  }

  const gradient = `conic-gradient(${stops.join(', ')})`;

  return (
    <div className="flex items-center gap-6">
      <div className="relative h-32 w-32 shrink-0 rounded-full" style={{ background: gradient }}>
        <div className="absolute inset-4 rounded-full bg-card" />
      </div>
      <div className="flex flex-col gap-1.5" key={JSON.stringify(sectors)}>
        {entries.map(([name, weight], i) => (
          <div key={name} className="flex items-center gap-2 text-sm">
            <span
              className="h-3 w-3 shrink-0 rounded-sm"
              style={{ backgroundColor: SECTOR_COLORS[i % SECTOR_COLORS.length] }}
              aria-hidden="true"
            />
            <span className="text-muted-foreground">{name}</span>
            <span className="ml-auto font-mono tabular-nums">{weight.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
