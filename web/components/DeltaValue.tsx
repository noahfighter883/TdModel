export function DeltaValue({
  value,
  digits = 1,
  suffix = "",
  size = "md",
  icon = true,
}: {
  value: number;
  digits?: number;
  suffix?: string;
  size?: "sm" | "md" | "lg";
  icon?: boolean;
}) {
  const positive = value > 0;
  const negative = value < 0;
  const color = positive ? "text-good" : negative ? "text-critical" : "text-text-secondary";
  const sizeClass = size === "lg" ? "text-2xl" : size === "sm" ? "text-xs" : "text-sm";

  return (
    <span className={`tabular inline-flex items-center gap-1 font-semibold ${color} ${sizeClass}`}>
      {icon && positive && <ArrowUp />}
      {icon && negative && <ArrowDown />}
      {positive ? "+" : ""}
      {value.toFixed(digits)}
      {suffix}
    </span>
  );
}

function ArrowUp() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
      <path d="M5 9V1M5 1L1.5 4.5M5 1L8.5 4.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ArrowDown() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
      <path d="M5 1V9M5 9L1.5 5.5M5 9L8.5 5.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
