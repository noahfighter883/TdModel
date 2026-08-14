const POSITION_COLORS: Record<string, string> = {
  RB: "bg-accent/15 text-accent border-accent/40",
  WR: "bg-good-dim text-good border-good/30",
  TE: "bg-critical-dim text-critical border-critical/30",
};

function initials(name: string) {
  const parts = name.replace(/[^a-zA-Z .]/g, "").split(" ").filter(Boolean);
  if (parts.length === 0) return "??";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function JerseyBadge({
  name,
  positionGroup,
  size = "md",
}: {
  name: string;
  positionGroup: string;
  size?: "sm" | "md" | "lg";
}) {
  const sizeClass = size === "lg" ? "h-20 w-20 text-2xl" : size === "sm" ? "h-9 w-9 text-xs" : "h-12 w-12 text-sm";
  const colorClass = POSITION_COLORS[positionGroup] ?? "bg-surface-raised text-text-secondary border-border-strong";

  return (
    <div
      className={`font-display flex shrink-0 items-center justify-center rounded-full border-2 font-bold tracking-tight ${sizeClass} ${colorClass}`}
    >
      {initials(name)}
    </div>
  );
}
