import Link from "next/link";
import type { Player } from "@/lib/data";
import { JerseyBadge } from "@/components/JerseyBadge";
import { DeltaValue } from "@/components/DeltaValue";
import { SignalBar } from "@/components/SignalBar";

export function Leaderboard({
  title,
  description,
  players,
  accentClass,
}: {
  title: string;
  description: string;
  players: Player[];
  accentClass: string;
}) {
  const max = Math.max(...players.map((p) => Math.abs(p.combinedSignal)), 1);

  return (
    <div className="rounded-xl border border-border bg-surface">
      <div className={`border-b border-border px-5 py-4 ${accentClass}`}>
        <h3 className="font-display text-lg font-bold text-text-primary">{title}</h3>
        <p className="mt-0.5 text-xs text-text-secondary">{description}</p>
      </div>
      <ol>
        {players.map((player, i) => (
          <li key={player.id} className="border-b border-border last:border-b-0">
            <Link
              href={`/players/${player.id}`}
              className="flex items-center gap-4 px-5 py-3.5 transition-colors hover:bg-surface-raised"
            >
              <span className="tabular w-5 shrink-0 text-right text-xs font-semibold text-text-muted">
                {i + 1}
              </span>
              <JerseyBadge name={player.name} positionGroup={player.positionGroup} size="sm" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-text-primary">{player.name}</p>
                <p className="text-xs text-text-muted">
                  {player.team} &middot; {player.position}
                </p>
              </div>
              <SignalBar value={player.combinedSignal} max={max} />
              <DeltaValue value={player.combinedSignal} suffix=" TD" />
            </Link>
          </li>
        ))}
      </ol>
    </div>
  );
}
