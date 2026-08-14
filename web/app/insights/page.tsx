import type { Metadata } from "next";
import Link from "next/link";
import { meta, players, topRisers, topFallers, biggestVegasDisagreements } from "@/lib/data";
import { StatTile } from "@/components/StatTile";
import { Leaderboard } from "@/components/Leaderboard";
import { JerseyBadge } from "@/components/JerseyBadge";
import { DeltaValue } from "@/components/DeltaValue";

export const metadata: Metadata = {
  title: "Insights | TD Regression",
  description: "The biggest positive and negative touchdown regression signals for 2026.",
};

export default function InsightsPage() {
  const risers = topRisers(12);
  const fallers = topFallers(12);
  const vegasDisagreements = biggestVegasDisagreements(8);

  const avgAbsSignal =
    players.reduce((sum, p) => sum + Math.abs(p.combinedSignal), 0) / players.length;

  return (
    <div className="mx-auto max-w-6xl px-6 py-14">
      <header className="max-w-2xl">
        <p className="text-sm font-semibold tracking-[0.2em] text-accent uppercase">Insights</p>
        <h1 className="font-display mt-2 text-4xl font-bold tracking-tight text-text-primary sm:text-5xl">
          The biggest movers
        </h1>
        <p className="mt-4 text-text-secondary">
          Ranked by combined signal &mdash; last season&apos;s actual-vs-expected touchdown gap,
          plus the projected shift in opportunity from who left and who joined their room.
        </p>
      </header>

      <div className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatTile label="Players scored" value={meta.playerCount} />
        <StatTile
          label="Strong buy signals"
          value={meta.labelCounts["Strong Positive (Buy)"]}
          sublabel="Top decile combined signal"
        />
        <StatTile
          label="Strong sell signals"
          value={meta.labelCounts["Strong Negative (Sell)"]}
          sublabel="Bottom decile combined signal"
        />
        <StatTile
          label="Avg. signal magnitude"
          value={`${avgAbsSignal.toFixed(1)} TD`}
          sublabel="Mean |combined signal|"
        />
      </div>

      <div className="mt-12 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Leaderboard
          title="Due for positive regression"
          description="Biggest combined signal &mdash; underperformed their xTD, gained opportunity, or both"
          players={risers}
          accentClass="bg-good-dim/30"
        />
        <Leaderboard
          title="Due for negative regression"
          description="Smallest combined signal &mdash; overperformed their xTD, lost opportunity, or both"
          players={fallers}
          accentClass="bg-critical-dim/30"
        />
      </div>

      <section className="mt-14">
        <h2 className="font-display text-2xl font-bold tracking-tight text-text-primary">
          Where we disagree with Vegas
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-text-secondary">
          Comparing our projected next-season touchdown total against{" "}
          {meta.vegasMatchedCount} matched season-long touchdown prop lines.
        </p>
        <div className="mt-6 overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-surface text-left text-xs text-text-muted uppercase">
                <th className="px-5 py-3 font-medium">Player</th>
                <th className="px-5 py-3 font-medium">Our projection</th>
                <th className="px-5 py-3 font-medium">Vegas line</th>
                <th className="px-5 py-3 font-medium">Difference</th>
              </tr>
            </thead>
            <tbody>
              {vegasDisagreements.map((player) => (
                <tr key={player.id} className="border-b border-border last:border-b-0 hover:bg-surface/60">
                  <td className="px-5 py-3">
                    <Link href={`/players/${player.id}`} className="flex items-center gap-3">
                      <JerseyBadge name={player.name} positionGroup={player.positionGroup} size="sm" />
                      <span>
                        <span className="font-semibold text-text-primary">{player.name}</span>
                        <span className="ml-2 text-xs text-text-muted">
                          {player.team} &middot; {player.position}
                        </span>
                      </span>
                    </Link>
                  </td>
                  <td className="tabular px-5 py-3 text-text-primary">
                    {player.projectedTd.toFixed(1)}
                  </td>
                  <td className="tabular px-5 py-3 text-text-secondary">
                    {player.vegas?.line.toFixed(1)}
                  </td>
                  <td className="px-5 py-3">
                    <DeltaValue value={player.vegas!.diff} suffix=" TD" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
