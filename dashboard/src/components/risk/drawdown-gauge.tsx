'use client';

const FILL_COLORS: Record<string, string> = {
  normal: 'oklch(0.75 0.18 180)',
  warning: 'oklch(0.78 0.15 75)',
  critical: 'oklch(0.65 0.22 25)',
};

const TEXT_CLASSES: Record<string, string> = {
  normal: 'text-profit',
  warning: 'text-interactive',
  critical: 'text-loss',
};

export function DrawdownGauge({ pct, level }: { pct: number; level: string }) {
  const clamped = Math.min(Math.max(pct, 0), 30);
  const degrees = (clamped / 30) * 180;
  const fillColor = FILL_COLORS[level] ?? FILL_COLORS.normal;
  const textClass = TEXT_CLASSES[level] ?? TEXT_CLASSES.normal;
  const trackColor = 'oklch(0.2 0.005 250)';

  const gradient = `conic-gradient(from 180deg, ${fillColor} 0deg ${degrees}deg, ${trackColor} ${degrees}deg 180deg, transparent 180deg)`;

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative h-20 w-40 overflow-hidden">
        <div key={pct} className="h-40 w-40 rounded-full" style={{ background: gradient }} />
        <div className="absolute inset-2 top-2 h-36 w-36 rounded-full bg-card" />
        <div className="absolute inset-0 flex items-end justify-center pb-1">
          <span className={`font-mono text-lg font-bold tabular-nums ${textClass}`}>
            {pct.toFixed(1)}%
          </span>
        </div>
      </div>
      <span className="text-xs text-muted-foreground">Drawdown</span>
    </div>
  );
}
