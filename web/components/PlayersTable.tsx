"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { Player } from "@/lib/data";
import { JerseyBadge } from "@/components/JerseyBadge";
import { RegressionBadge } from "@/components/RegressionBadge";
import { DeltaValue } from "@/components/DeltaValue";
import { SignalBar } from "@/components/SignalBar";

type SortKey = "combinedSignal" | "actualTd" | "xtd" | "opportunities" | "name" | "vegasDiff";
type PositionFilter = "ALL" | "RB" | "WR" | "TE";

const POSITION_TABS: PositionFilter[] = ["ALL", "RB", "WR", "TE"];

function sortValue(player: Player, key: SortKey): number | string | null {
  if (key === "name") return player.name;
  if (key === "vegasDiff") return player.vegas?.diff ?? null;
  return player[key];
}

export function PlayersTable({ players }: { players: Player[] }) {
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState<PositionFilter>("ALL");
  const [sortKey, setSortKey] = useState<SortKey>("combinedSignal");
  const [sortDir, setSortDir] = useState<1 | -1>(-1);

  const maxSignal = useMemo(
    () => Math.max(...players.map((p) => Math.abs(p.combinedSignal)), 1),
    [players]
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return players
      .filter((p) => position === "ALL" || p.positionGroup === position)
      .filter((p) => !q || p.name.toLowerCase().includes(q) || p.team.toLowerCase().includes(q))
      .sort((a, b) => {
        const va = sortValue(a, sortKey);
        const vb = sortValue(b, sortKey);
        // Players without a matched Vegas line always sort to the bottom.
        if (va === null && vb === null) return 0;
        if (va === null) return 1;
        if (vb === null) return -1;
        if (typeof va === "string" || typeof vb === "string") {
          return sortDir * String(va).localeCompare(String(vb));
        }
        return sortDir * (va - vb);
      });
  }, [players, query, position, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === 1 ? -1 : 1));
    } else {
      setSortKey(key);
      setSortDir(-1);
    }
  }

  return (
    <div>
      <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-1 rounded-lg border border-border bg-surface p-1">
          {POSITION_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setPosition(tab)}
              className={`rounded-md px-3.5 py-1.5 text-sm font-semibold transition-colors ${
                position === tab
                  ? "bg-accent text-bg"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {tab === "ALL" ? "All positions" : tab}
            </button>
          ))}
        </div>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search player or team&hellip;"
          className="w-full rounded-lg border border-border-strong bg-surface px-4 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none sm:w-64"
        />
      </div>

      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full min-w-[940px] text-sm">
          <thead>
            <tr className="border-b border-border bg-surface text-left text-xs text-text-muted uppercase">
              <SortableHeader label="Player" active={sortKey === "name"} dir={sortDir} onClick={() => toggleSort("name")} />
              <th className="px-4 py-3 font-medium">Team</th>
              <SortableHeader label="Opp" active={sortKey === "opportunities"} dir={sortDir} onClick={() => toggleSort("opportunities")} align="right" />
              <SortableHeader label="Actual TD" active={sortKey === "actualTd"} dir={sortDir} onClick={() => toggleSort("actualTd")} align="right" />
              <SortableHeader label="xTD" active={sortKey === "xtd"} dir={sortDir} onClick={() => toggleSort("xtd")} align="right" />
              <SortableHeader label="Signal" active={sortKey === "combinedSignal"} dir={sortDir} onClick={() => toggleSort("combinedSignal")} />
              <th className="px-4 py-3 text-right font-medium">Vegas line</th>
              <SortableHeader label="vs Vegas" active={sortKey === "vegasDiff"} dir={sortDir} onClick={() => toggleSort("vegasDiff")} align="right" />
              <th className="px-4 py-3 font-medium">Read</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((player) => (
              <tr key={player.id} className="border-b border-border last:border-b-0 hover:bg-surface/60">
                <td className="px-4 py-3">
                  <Link href={`/players/${player.id}`} className="flex items-center gap-3">
                    <JerseyBadge name={player.name} positionGroup={player.positionGroup} size="sm" />
                    <span className="min-w-0">
                      <span className="block truncate font-semibold text-text-primary">
                        {player.name}
                      </span>
                      <span className="text-xs text-text-muted">{player.position}</span>
                    </span>
                  </Link>
                </td>
                <td className="px-4 py-3 text-text-secondary">{player.team}</td>
                <td className="tabular px-4 py-3 text-right text-text-secondary">
                  {player.opportunities}
                </td>
                <td className="tabular px-4 py-3 text-right text-text-primary">{player.actualTd}</td>
                <td className="tabular px-4 py-3 text-right text-text-secondary">
                  {player.xtd.toFixed(1)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <SignalBar value={player.combinedSignal} max={maxSignal} />
                    <DeltaValue value={player.combinedSignal} size="sm" />
                  </div>
                </td>
                <td className="tabular px-4 py-3 text-right text-text-secondary">
                  {player.vegas ? player.vegas.line.toFixed(1) : <span className="text-text-muted">&mdash;</span>}
                </td>
                <td className="px-4 py-3 text-right">
                  {player.vegas ? (
                    <DeltaValue value={player.vegas.diff} size="sm" />
                  ) : (
                    <span className="text-xs text-text-muted">&mdash;</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <RegressionBadge label={player.label} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p className="px-4 py-10 text-center text-sm text-text-muted">
            No players match &ldquo;{query}&rdquo;.
          </p>
        )}
      </div>
      <p className="mt-3 text-xs text-text-muted">
        Showing {filtered.length} of {players.length} players.
      </p>
    </div>
  );
}

function SortableHeader({
  label,
  active,
  dir,
  onClick,
  align = "left",
}: {
  label: string;
  active: boolean;
  dir: 1 | -1;
  onClick: () => void;
  align?: "left" | "right";
}) {
  return (
    <th className={`px-4 py-3 font-medium ${align === "right" ? "text-right" : "text-left"}`}>
      <button
        onClick={onClick}
        className={`inline-flex items-center gap-1 transition-colors hover:text-text-primary ${
          active ? "text-text-primary" : ""
        }`}
      >
        {label}
        {active && <span aria-hidden="true">{dir === 1 ? "↑" : "↓"}</span>}
      </button>
    </th>
  );
}
