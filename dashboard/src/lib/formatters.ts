const currencyFmt = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const percentFmt = new Intl.NumberFormat('en-US', {
  style: 'percent',
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const scoreFmt = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export function formatCurrency(value: number): string {
  if (!Number.isFinite(value)) return '$0.00';
  return currencyFmt.format(value);
}

export function formatPercent(value: number): string {
  if (!Number.isFinite(value)) return '0.0%';
  return percentFmt.format(value / 100);
}

export function formatScore(value: number): string {
  if (!Number.isFinite(value)) return '0.0';
  return scoreFmt.format(value);
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '--';
  return dateStr.slice(0, 10);
}
