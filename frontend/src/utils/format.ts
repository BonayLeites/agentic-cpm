export function formatDuration(ms: number | null): string {
  if (ms == null) return "—";
  return `${(ms / 1000).toFixed(1)}s`;
}

export function formatConfidence(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${Math.round(Number(v))}%`;
}
