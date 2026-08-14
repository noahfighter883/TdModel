"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { Player } from "@/lib/data";

type PositionFilter = "RB" | "WR" | "TE";

const POSITION_TABS: PositionFilter[] = ["RB", "WR", "TE"];

const SIZE = 560;
const MARGIN = { top: 16, right: 20, bottom: 44, left: 52 };
const VIEW_W = MARGIN.left + SIZE + MARGIN.right;
const VIEW_H = MARGIN.top + SIZE + MARGIN.bottom;
const OVER_UNDER_THRESHOLD = 0.3; // TD gap below which a player reads as "on the line"

export function ActualVsExpectedChart({ players }: { players: Player[] }) {
  const router = useRouter();
  const [position, setPosition] = useState<PositionFilter>("RB");
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const group = useMemo(
    () => players.filter((p) => p.positionGroup === position),
    [players, position]
  );

  const maxVal = useMemo(() => {
    const raw = Math.max(...group.map((p) => Math.max(p.xtd, p.actualTd)), 1);
    return Math.ceil((raw * 1.08) / 2) * 2;
  }, [group]);

  const scaleX = (v: number) => MARGIN.left + (v / maxVal) * SIZE;
  const scaleY = (v: number) => MARGIN.top + SIZE - (v / maxVal) * SIZE;

  const ticks = useMemo(() => {
    const step = maxVal / 5;
    return Array.from({ length: 6 }, (_, i) => Math.round(i * step));
  }, [maxVal]);

  const { labelAbove, labelBelow } = useMemo(() => {
    const sorted = [...group].sort((a, b) => a.actualTd - a.xtd - (b.actualTd - b.xtd));
    return {
      labelBelow: sorted.slice(0, 3).map((p) => p.id), // most underperformed (actual << xtd)
      labelAbove: sorted.slice(-3).map((p) => p.id), // most overperformed (actual >> xtd)
    };
  }, [group]);

  const hovered = group.find((p) => p.id === hoveredId) ?? null;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex gap-1 rounded-lg border border-border bg-surface p-1">
          {POSITION_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setPosition(tab)}
              className={`rounded-md px-4 py-1.5 text-sm font-semibold transition-colors ${
                position === tab
                  ? "bg-accent text-bg"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
        <Legend />
      </div>

      <div className="relative mt-6 rounded-xl border border-border bg-surface p-4 sm:p-6">
        <svg
          viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
          className="w-full"
          role="img"
          aria-label={`Scatter plot of actual vs. expected touchdowns for ${position}s`}
        >
          {/* gridlines + axis ticks */}
          {ticks.map((t) => (
            <g key={t}>
              <line
                x1={scaleX(t)}
                y1={MARGIN.top}
                x2={scaleX(t)}
                y2={MARGIN.top + SIZE}
                stroke="var(--border)"
                strokeWidth={1}
              />
              <line
                x1={MARGIN.left}
                y1={scaleY(t)}
                x2={MARGIN.left + SIZE}
                y2={scaleY(t)}
                stroke="var(--border)"
                strokeWidth={1}
              />
              <text
                x={scaleX(t)}
                y={MARGIN.top + SIZE + 20}
                textAnchor="middle"
                className="fill-text-muted"
                fontSize={12}
              >
                {t}
              </text>
              <text
                x={MARGIN.left - 10}
                y={scaleY(t)}
                textAnchor="end"
                dominantBaseline="middle"
                className="fill-text-muted"
                fontSize={12}
              >
                {t}
              </text>
            </g>
          ))}

          {/* axis titles */}
          <text
            x={MARGIN.left + SIZE / 2}
            y={VIEW_H - 4}
            textAnchor="middle"
            className="fill-text-secondary"
            fontSize={12}
            fontWeight={600}
          >
            Expected touchdowns (xTD)
          </text>
          <text
            x={14}
            y={MARGIN.top + SIZE / 2}
            textAnchor="middle"
            className="fill-text-secondary"
            fontSize={12}
            fontWeight={600}
            transform={`rotate(-90, 14, ${MARGIN.top + SIZE / 2})`}
          >
            Actual touchdowns
          </text>

          {/* y = x reference line */}
          <line
            x1={scaleX(0)}
            y1={scaleY(0)}
            x2={scaleX(maxVal)}
            y2={scaleY(maxVal)}
            stroke="var(--border-strong)"
            strokeWidth={2}
            strokeDasharray="4 4"
          />

          {/* points */}
          {group.map((p) => {
            const gap = p.actualTd - p.xtd;
            const colorClass =
              gap > OVER_UNDER_THRESHOLD
                ? "fill-critical"
                : gap < -OVER_UNDER_THRESHOLD
                  ? "fill-good"
                  : "fill-text-secondary";
            const isHovered = p.id === hoveredId;
            const showLabel = labelAbove.includes(p.id) || labelBelow.includes(p.id);
            const cx = scaleX(p.xtd);
            const cy = scaleY(p.actualTd);

            return (
              <g key={p.id}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered ? 7 : 5}
                  className={colorClass}
                  stroke="var(--surface)"
                  strokeWidth={1.5}
                  onMouseEnter={() => setHoveredId(p.id)}
                  onMouseLeave={() => setHoveredId((id) => (id === p.id ? null : id))}
                  onClick={() => router.push(`/players/${p.id}`)}
                  style={{ cursor: "pointer" }}
                />
                {showLabel && (
                  <text
                    x={cx}
                    y={gap > 0 ? cy - 10 : cy + 16}
                    textAnchor="middle"
                    className="fill-text-secondary"
                    fontSize={11}
                    pointerEvents="none"
                  >
                    {p.name}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {hovered && (
          <div
            className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-lg border border-border-strong bg-surface-raised px-3 py-2 text-xs shadow-lg"
            style={{
              left: `${(scaleX(hovered.xtd) / VIEW_W) * 100}%`,
              top: `${(scaleY(hovered.actualTd) / VIEW_H) * 100}%`,
              marginTop: -10,
            }}
          >
            <p className="font-semibold text-text-primary">{hovered.name}</p>
            <p className="mt-0.5 text-text-muted">
              {hovered.team} &middot; {hovered.position}
            </p>
            <p className="tabular mt-1 text-text-secondary">
              {hovered.actualTd} actual &middot; {hovered.xtd.toFixed(1)} xTD
            </p>
          </div>
        )}
      </div>

      <p className="mt-3 text-xs text-text-muted">
        Each dot is a player. See the full numbers in the{" "}
        <Link href="/players" className="text-text-secondary underline hover:text-text-primary">
          player table
        </Link>
        .
      </p>
    </div>
  );
}

function Legend() {
  return (
    <div className="flex flex-wrap items-center gap-4 text-xs text-text-secondary">
      <span className="inline-flex items-center gap-1.5">
        <span className="h-2 w-2 rounded-full bg-good" />
        Below the line &mdash; underperformed, due for positive regression
      </span>
      <span className="inline-flex items-center gap-1.5">
        <span className="h-2 w-2 rounded-full bg-critical" />
        Above the line &mdash; overperformed, due for negative regression
      </span>
    </div>
  );
}
