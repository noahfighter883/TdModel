import Link from "next/link";
import { meta, topRisers, topFallers } from "@/lib/data";
import { RegressionBadge } from "@/components/RegressionBadge";
import { DeltaValue } from "@/components/DeltaValue";
import { JerseyBadge } from "@/components/JerseyBadge";

export default function Home() {
  const riser = topRisers(1)[0];
  const faller = topFallers(1)[0];
  const strongSignals =
    meta.labelCounts["Strong Positive (Buy)"] + meta.labelCounts["Strong Negative (Sell)"];

  return (
    <>
      <Hero strongSignals={strongSignals} />
      <PreviewStrip riser={riser} faller={faller} />
      <MethodologySection />
      <PipelineSection />
      <ClosingCta />
    </>
  );
}

function Hero({ strongSignals }: { strongSignals: number }) {
  return (
    <section className="border-b border-border">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:py-28">
        <p className="mb-5 text-sm font-semibold tracking-[0.2em] text-accent uppercase">
          {meta.seasonPrior} touchdowns vs. {meta.seasonNext} opportunity
        </p>
        <h1 className="font-display max-w-4xl text-5xl leading-[0.95] font-extrabold tracking-tight text-text-primary sm:text-7xl">
          Touchdowns lie.
          <br />
          Opportunity doesn&apos;t.
        </h1>
        <p className="mt-7 max-w-2xl text-lg leading-relaxed text-text-secondary">
          Every rush and target near the goal line carries its own historical
          scoring probability. We total that up into an expected touchdown
          count for every skill-position player, then adjust it for who left
          and who joined their backfield or receiving room &mdash; to find who&apos;s
          about to score a lot more, or a lot less, than last year.
        </p>
        <div className="mt-9 flex flex-wrap items-center gap-4">
          <Link
            href="/insights"
            className="rounded-lg bg-accent px-5 py-3 text-sm font-semibold text-bg transition-colors hover:bg-accent-strong"
          >
            See the biggest movers
          </Link>
          <Link
            href="/players"
            className="rounded-lg border border-border-strong px-5 py-3 text-sm font-semibold text-text-primary transition-colors hover:bg-surface"
          >
            Browse every player
          </Link>
        </div>

        <dl className="mt-16 grid grid-cols-2 gap-8 sm:grid-cols-4">
          <Stat label="Players scored" value={meta.playerCount} />
          <Stat label="Seasons of play-by-play" value={`${meta.histSeasons[1] - meta.histSeasons[0] + 1}`} />
          <Stat label="Strong signals" value={strongSignals} />
          <Stat label="Matched to Vegas lines" value={meta.vegasMatchedCount} />
        </dl>
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <dt className="text-xs font-medium tracking-wide text-text-muted uppercase">{label}</dt>
      <dd className="font-display tabular mt-1 text-4xl font-bold text-text-primary">{value}</dd>
    </div>
  );
}

function PreviewStrip({
  riser,
  faller,
}: {
  riser: ReturnType<typeof topRisers>[number];
  faller: ReturnType<typeof topFallers>[number];
}) {
  return (
    <section className="border-b border-border bg-surface/40">
      <div className="mx-auto grid max-w-6xl grid-cols-1 divide-y divide-border sm:grid-cols-2 sm:divide-x sm:divide-y-0">
        <PreviewCard
          eyebrow="Most due for a bounce-back"
          player={riser}
          signalLabel="Combined signal"
        />
        <PreviewCard
          eyebrow="Most due to come back to earth"
          player={faller}
          signalLabel="Combined signal"
        />
      </div>
    </section>
  );
}

function PreviewCard({
  eyebrow,
  player,
  signalLabel,
}: {
  eyebrow: string;
  player: ReturnType<typeof topRisers>[number];
  signalLabel: string;
}) {
  return (
    <Link
      href={`/players/${player.id}`}
      className="group flex items-center gap-5 px-6 py-8 transition-colors hover:bg-surface sm:px-10"
    >
      <JerseyBadge name={player.name} positionGroup={player.positionGroup} size="lg" />
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium tracking-wide text-text-muted uppercase">{eyebrow}</p>
        <p className="font-display mt-1 truncate text-2xl font-bold text-text-primary group-hover:text-accent">
          {player.name}
        </p>
        <p className="mt-0.5 text-sm text-text-secondary">
          {player.team} &middot; {player.position} &middot; {player.actualTd} actual TD vs{" "}
          {player.xtd.toFixed(1)} xTD
        </p>
        <div className="mt-3 flex items-center gap-3">
          <RegressionBadge label={player.label} />
          <span className="text-xs text-text-muted">{signalLabel}</span>
          <DeltaValue value={player.combinedSignal} suffix=" TD" />
        </div>
      </div>
    </Link>
  );
}

function MethodologySection() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20">
      <h2 className="font-display max-w-xl text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">
        Three signals, one number
      </h2>
      <p className="mt-3 max-w-2xl text-text-secondary">
        A player&apos;s combined signal is the sum of how lucky they got last
        season and how much their opportunity is about to shift.
      </p>

      <div className="mt-10 grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-border bg-border md:grid-cols-3">
        <MethodCard
          title="Efficiency"
          formula="xTD − actual TD"
          color="accent"
          body="Every opportunity is weighted by the historical score rate at its exact yard line. Score way more than that baseline predicted and you were lucky; score way less and positive regression is likely coming."
        />
        <MethodCard
          title="Vacated"
          formula="+ departed teammates' share"
          color="good"
          body="When a same-position teammate leaves — cut, retired, traded, signed elsewhere — their share of the team's red-zone work is redistributed to whoever's left, proportional to their existing role."
        />
        <MethodCard
          title="Stolen"
          formula="− new arrivals' share"
          color="critical"
          body="When a team drafts or signs a new same-position player, we estimate the share they're likely to take — from rookie draft capital or their own usage on their old team — and dock it from the incumbents."
        />
      </div>
    </section>
  );
}

function MethodCard({
  title,
  formula,
  body,
  color,
}: {
  title: string;
  formula: string;
  body: string;
  color: "accent" | "good" | "critical";
}) {
  const dotClass = { accent: "bg-accent", good: "bg-good", critical: "bg-critical" }[color];
  return (
    <div className="bg-bg p-8">
      <div className="flex items-center gap-2.5">
        <span className={`h-2 w-2 rounded-full ${dotClass}`} />
        <h3 className="font-display text-xl font-bold text-text-primary">{title}</h3>
      </div>
      <p className="tabular mt-2 text-sm font-medium text-text-muted">{formula}</p>
      <p className="mt-4 text-sm leading-relaxed text-text-secondary">{body}</p>
    </div>
  );
}

const PIPELINE_STEPS = [
  {
    step: "01",
    title: "Score every play",
    body: "10 seasons of play-by-play, one row per rush attempt or target, weighted by the empirical touchdown rate at that yard line.",
  },
  {
    step: "02",
    title: "Sum to xTD",
    body: "Each player's opportunities roll up into a season expected-touchdown total, compared against what they actually scored.",
  },
  {
    step: "03",
    title: "Diff the rosters",
    body: "Compare last year's and this year's team rosters at RB, WR, and TE to find who left and who arrived.",
  },
  {
    step: "04",
    title: "Redistribute share",
    body: "Departed players' share flows to the incumbents who stayed; incoming players' projected share is docked from them.",
  },
];

function PipelineSection() {
  return (
    <section className="border-y border-border bg-surface/40">
      <div className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="font-display text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">
          How the pipeline runs
        </h2>
        <div className="mt-10 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {PIPELINE_STEPS.map((s, i) => (
            <div key={s.step} className="relative">
              <p className="font-display tabular text-5xl font-extrabold text-border-strong">{s.step}</p>
              <h3 className="font-display mt-2 text-lg font-bold text-text-primary">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-secondary">{s.body}</p>
              {i < PIPELINE_STEPS.length - 1 && (
                <div className="yard-rule mt-6 hidden lg:block" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ClosingCta() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20 text-center">
      <h2 className="font-display text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">
        Ready to see who&apos;s due?
      </h2>
      <p className="mx-auto mt-3 max-w-xl text-text-secondary">
        Rank every same-team RB, WR, and TE by combined signal, or jump
        straight to the full table.
      </p>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
        <Link
          href="/insights"
          className="rounded-lg bg-accent px-5 py-3 text-sm font-semibold text-bg transition-colors hover:bg-accent-strong"
        >
          View insights
        </Link>
        <Link
          href="/players"
          className="rounded-lg border border-border-strong px-5 py-3 text-sm font-semibold text-text-primary transition-colors hover:bg-surface"
        >
          Full player table
        </Link>
      </div>
    </section>
  );
}
