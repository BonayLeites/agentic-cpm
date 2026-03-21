interface ConfidenceBarProps {
  value: number | string | null | undefined;
  showLabel?: boolean;
}

export default function ConfidenceBar({ value, showLabel = true }: ConfidenceBarProps) {
  const num = Number(value ?? 0);
  const pct = Math.min(Math.max(num, 0), 100);

  const color =
    pct >= 80
      ? "bg-emerald-500"
      : pct >= 60
        ? "bg-amber-500"
        : "bg-red-500";

  const trackColor =
    pct >= 80
      ? "bg-emerald-100"
      : pct >= 60
        ? "bg-amber-100"
        : "bg-red-100";

  return (
    <div className="flex items-center gap-2">
      <div className={`h-1.5 w-16 overflow-hidden rounded-full ${trackColor}`}>
        <div
          className={`h-full rounded-full ${color} transition-all duration-300`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs tabular-nums text-gray-500">{Math.round(pct)}%</span>
      )}
    </div>
  );
}
