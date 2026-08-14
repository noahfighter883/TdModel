/** Diverging bar anchored to a center baseline, used inline in the players
 * table to show combinedSignal magnitude relative to the rest of the pool. */
export function SignalBar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? Math.min(Math.abs(value) / max, 1) * 100 : 0;
  const positive = value >= 0;

  return (
    <div className="relative h-4 w-24 shrink-0" aria-hidden="true">
      <div className="absolute left-1/2 top-1/2 h-3.5 w-px -translate-x-1/2 -translate-y-1/2 bg-border-strong" />
      <div className="absolute inset-y-0 left-1/2 flex w-1/2 items-center justify-start pl-[1px]">
        {positive && (
          <div
            className="h-1.5 rounded-r-full bg-good"
            style={{ width: `${pct / 2}%` }}
          />
        )}
      </div>
      <div className="absolute inset-y-0 right-1/2 flex w-1/2 items-center justify-end pr-[1px]">
        {!positive && (
          <div
            className="h-1.5 rounded-l-full bg-critical"
            style={{ width: `${pct / 2}%` }}
          />
        )}
      </div>
    </div>
  );
}
