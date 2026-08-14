import type { Metadata } from "next";
import { players } from "@/lib/data";
import { PlayersTable } from "@/components/PlayersTable";

export const metadata: Metadata = {
  title: "All players | TD Regression",
  description: "Every scored RB, WR, and TE, sortable by touchdown regression signal.",
};

export default function PlayersPage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-14">
      <header className="max-w-2xl">
        <p className="text-sm font-semibold tracking-[0.2em] text-accent uppercase">
          Full table
        </p>
        <h1 className="font-display mt-2 text-4xl font-bold tracking-tight text-text-primary sm:text-5xl">
          Every player
        </h1>
        <p className="mt-4 text-text-secondary">
          All {players.length} same-team RB, WR, and TE players with at least 30 opportunities
          last season. Sort by any column, or click a row for the full breakdown.
        </p>
      </header>

      <div className="mt-10">
        <PlayersTable players={players} />
      </div>
    </div>
  );
}
