import playersRaw from "@/data/players.json";
import metaRaw from "@/data/meta.json";

export type RegressionLabel =
  | "Strong Positive (Buy)"
  | "Positive"
  | "Neutral"
  | "Negative"
  | "Strong Negative (Sell)";

export interface VegasLine {
  line: number;
  market: "rush_rec" | "rush_only" | "rec_only";
  diff: number;
}

export interface Player {
  id: string;
  name: string;
  team: string;
  position: string;
  positionGroup: "RB" | "WR" | "TE";
  seasonPrior: number;
  seasonNext: number;
  opportunities: number;
  actualTd: number;
  xtd: number;
  efficiencySignal: number;
  priorGroupShare: number;
  teamGroupXtdPool: number;
  vacatedShareGained: number;
  stolenShareLost: number;
  netShareChange: number;
  opportunitySignal: number;
  combinedSignal: number;
  projectedTd: number;
  label: RegressionLabel;
  vegas: VegasLine | null;
}

export interface Meta {
  generatedAt: string;
  seasonPrior: number;
  seasonNext: number;
  playerCount: number;
  labelCounts: Record<RegressionLabel, number>;
  vegasMatchedCount: number;
  histSeasons: [number, number];
  minOpportunities: number;
}

export const players = playersRaw as Player[];
export const meta = metaRaw as Meta;

export function getPlayer(id: string): Player | undefined {
  return players.find((p) => p.id === id);
}

export function topRisers(n: number): Player[] {
  return [...players].sort((a, b) => b.combinedSignal - a.combinedSignal).slice(0, n);
}

export function topFallers(n: number): Player[] {
  return [...players].sort((a, b) => a.combinedSignal - b.combinedSignal).slice(0, n);
}

export function biggestVegasDisagreements(n: number): Player[] {
  return [...players]
    .filter((p) => p.vegas !== null)
    .sort((a, b) => Math.abs(b.vegas!.diff) - Math.abs(a.vegas!.diff))
    .slice(0, n);
}
