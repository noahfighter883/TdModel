/** Paired horizontal bars on one shared scale: actual TDs vs xTD. */
export function ComparisonBars({ actual, xtd }: { actual: number; xtd: number }) {
  const max = Math.max(actual, xtd, 1) * 1.15;
  const actualPct = (actual / max) * 100;
  const xtdPct = (xtd / max) * 100;

  return (
    <div className="flex flex-col gap-3">
      <BarRow label="Actual TDs" value={actual} pct={actualPct} colorClass="bg-accent" />
      <BarRow label="Expected (xTD)" value={xtd} pct={xtdPct} colorClass="bg-text-secondary" />
    </div>
  );
}

function BarRow({
  label,
  value,
  pct,
  colorClass,
}: {
  label: string;
  value: number;
  pct: number;
  colorClass: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-32 shrink-0 text-xs text-text-secondary">{label}</span>
      <div className="h-3 flex-1 rounded-full bg-surface-raised">
        <div
          className={`h-3 rounded-full ${colorClass}`}
          style={{ width: `${Math.max(pct, 2)}%` }}
        />
      </div>
      <span className="tabular w-12 shrink-0 text-right text-sm font-semibold text-text-primary">
        {value.toFixed(1)}
      </span>
    </div>
  );
}
