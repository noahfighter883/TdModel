import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getPlayer, players } from "@/lib/data";
import { JerseyBadge } from "@/components/JerseyBadge";
import { RegressionBadge } from "@/components/RegressionBadge";
import { DeltaValue } from "@/components/DeltaValue";
import { ComparisonBars } from "@/components/ComparisonBars";
import { StatTile } from "@/components/StatTile";

export function generateStaticParams() {
  return players.map((p) => ({ id: p.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const player = getPlayer(id);
  if (!player) return { title: "Player not found | TD Regression" };
  return {
    title: `${player.name} | TD Regression`,
    description: `${player.name} (${player.team} ${player.position}): ${player.actualTd} actual touchdowns vs ${player.xtd.toFixed(1)} expected in ${player.seasonPrior}.`,
  };
}

export default async function PlayerPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const player = getPlayer(id);
  if (!player) notFound();

  const shareGap = player.netShareChange;

  return (
    <div className="mx-auto max-w-4xl px-6 py-14">
      <Link href="/players" className="text-sm text-text-secondary hover:text-text-primary">
        &larr; All players
      </Link>

      <div className="mt-6 flex flex-wrap items-center gap-5">
        <JerseyBadge name={player.name} positionGroup={player.positionGroup} size="lg" />
        <div>
          <h1 className="font-display text-4xl font-bold tracking-tight text-text-primary sm:text-5xl">
            {player.name}
          </h1>
          <p className="mt-1 text-text-secondary">
            {player.team} &middot; {player.position} &middot; {player.opportunities} opportunities
            in {player.seasonPrior}
          </p>
        </div>
        <div className="ml-auto flex flex-col items-end gap-2">
          <RegressionBadge label={player.label} full />
          <DeltaValue value={player.combinedSignal} suffix=" TD combined signal" size="lg" />
        </div>
      </div>

      <div className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatTile label="Actual TDs" value={player.actualTd} sublabel={player.seasonPrior.toString()} />
        <StatTile label="Expected (xTD)" value={player.xtd.toFixed(1)} sublabel="From play-by-play" />
        <StatTile
          label="Efficiency signal"
          value={
            <DeltaValue value={player.efficiencySignal} suffix=" TD" />
          }
          sublabel="xTD − actual"
        />
        <StatTile
          label="Projected TD"
          value={player.projectedTd.toFixed(1)}
          sublabel={player.seasonNext.toString()}
        />
      </div>

      <section className="mt-12">
        <h2 className="font-display text-2xl font-bold tracking-tight text-text-primary">
          Efficiency: actual vs. expected
        </h2>
        <p className="mt-2 max-w-xl text-sm text-text-secondary">
          {player.efficiencySignal > 0.5
            ? `${player.name} scored well below their expected rate — a classic setup for positive touchdown regression.`
            : player.efficiencySignal < -0.5
              ? `${player.name} scored well above their expected rate — history says that gap tends to close.`
              : `${player.name}'s actual touchdowns tracked closely with their expected rate — no strong efficiency signal either way.`}
        </p>
        <div className="mt-6 rounded-xl border border-border bg-surface p-6">
          <ComparisonBars actual={player.actualTd} xtd={player.xtd} />
        </div>
      </section>

      <section className="mt-12">
        <h2 className="font-display text-2xl font-bold tracking-tight text-text-primary">
          Opportunity shift
        </h2>
        <p className="mt-2 max-w-xl text-sm text-text-secondary">
          Held {(player.priorGroupShare * 100).toFixed(0)}% of {player.team}&apos;s{" "}
          {player.positionGroup} touchdown opportunity in {player.seasonPrior}, out of a{" "}
          {player.teamGroupXtdPool.toFixed(1)} xTD team pool.
        </p>
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <ShareTile
            label="Gained from departures"
            value={player.vacatedShareGained}
            tone="good"
          />
          <ShareTile label="Lost to new arrivals" value={-player.stolenShareLost} tone="critical" />
          <ShareTile label="Net opportunity change" value={shareGap} tone="neutral" />
        </div>
      </section>

      {player.vegas && (
        <section className="mt-12">
          <h2 className="font-display text-2xl font-bold tracking-tight text-text-primary">
            Vs. the market
          </h2>
          <div className="mt-6 flex flex-wrap items-center gap-8 rounded-xl border border-border bg-surface p-6">
            <div>
              <p className="text-xs font-medium tracking-wide text-text-muted uppercase">
                Our projection
              </p>
              <p className="font-display tabular mt-1 text-3xl font-bold text-text-primary">
                {player.projectedTd.toFixed(1)}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium tracking-wide text-text-muted uppercase">
                Vegas line
              </p>
              <p className="font-display tabular mt-1 text-3xl font-bold text-text-secondary">
                {player.vegas.line.toFixed(1)}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium tracking-wide text-text-muted uppercase">
                Difference
              </p>
              <p className="mt-1">
                <DeltaValue value={player.vegas.diff} suffix=" TD" size="lg" />
              </p>
            </div>
            <p className="w-full text-xs text-text-muted">
              Market: {marketLabel(player.vegas.market)}
            </p>
          </div>
        </section>
      )}
    </div>
  );
}

function ShareTile({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "good" | "critical" | "neutral";
}) {
  const toneClass =
    tone === "good" ? "text-good" : tone === "critical" ? "text-critical" : "text-text-primary";
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <p className="text-xs font-medium tracking-wide text-text-muted uppercase">{label}</p>
      <p className={`font-display tabular mt-1.5 text-2xl font-bold ${toneClass}`}>
        {value > 0 ? "+" : ""}
        {(value * 100).toFixed(1)}%
      </p>
    </div>
  );
}

function marketLabel(market: string) {
  if (market === "rush_rec") return "Season rushing + receiving TDs";
  if (market === "rush_only") return "Season rushing TDs";
  return "Season receiving TDs";
}
