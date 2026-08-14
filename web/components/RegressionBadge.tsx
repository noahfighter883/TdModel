import type { RegressionLabel } from "@/lib/data";

const STYLES: Record<RegressionLabel, string> = {
  "Strong Positive (Buy)": "bg-good-dim text-good border-good/40",
  Positive: "bg-good-dim/60 text-good border-good/20",
  Neutral: "bg-surface-raised text-text-secondary border-border-strong",
  Negative: "bg-critical-dim/60 text-critical border-critical/20",
  "Strong Negative (Sell)": "bg-critical-dim text-critical border-critical/40",
};

const SHORT: Record<RegressionLabel, string> = {
  "Strong Positive (Buy)": "Strong buy",
  Positive: "Positive",
  Neutral: "Neutral",
  Negative: "Negative",
  "Strong Negative (Sell)": "Strong sell",
};

export function RegressionBadge({
  label,
  full = false,
}: {
  label: RegressionLabel;
  full?: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-wide whitespace-nowrap ${STYLES[label]}`}
    >
      {full ? label : SHORT[label]}
    </span>
  );
}
