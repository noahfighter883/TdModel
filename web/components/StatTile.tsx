import type { ReactNode } from "react";

export function StatTile({
  label,
  value,
  sublabel,
}: {
  label: string;
  value: ReactNode;
  sublabel?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <p className="text-xs font-medium tracking-wide text-text-muted uppercase">{label}</p>
      <p className="font-display tabular mt-1.5 text-3xl font-bold text-text-primary">{value}</p>
      {sublabel && <p className="mt-1 text-xs text-text-secondary">{sublabel}</p>}
    </div>
  );
}
