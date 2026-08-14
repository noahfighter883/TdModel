"""Exports the scoring table + Vegas comparison as JSON for the web app
(web/data/players.json), rounded and renamed to camelCase for direct use in
TypeScript without a server-side data layer.
"""

import json
from datetime import datetime, timezone

import polars as pl

from tdmodel import config

WEB_DATA_DIR = config.ROOT / "web" / "data"


def _round(v, ndigits):
    return None if v is None else round(float(v), ndigits)


def build_players_payload() -> list[dict]:
    scoring = pl.read_csv(config.DATA_OUTPUT / f"td_regression_{config.NEXT_SEASON}.csv")
    vegas_path = config.DATA_OUTPUT / "vegas_comparison_2026.csv"
    vegas = pl.read_csv(vegas_path) if vegas_path.exists() else None
    vegas_by_id = {row["player_id"]: row for row in vegas.to_dicts()} if vegas is not None else {}

    players = []
    for row in scoring.to_dicts():
        v = vegas_by_id.get(row["player_id"])
        players.append(
            {
                "id": row["player_id"],
                "name": row["player_name"],
                "team": row["team"],
                "position": row["position"],
                "positionGroup": row["position_group"],
                "seasonPrior": row["season_prior"],
                "seasonNext": row["season_next"],
                "opportunities": row["opportunities_prior"],
                "actualTd": row["actual_td_prior"],
                "xtd": _round(row["xtd_prior"], 2),
                "efficiencySignal": _round(row["regression_signal_efficiency"], 2),
                "priorGroupShare": _round(row["prior_group_share"], 3),
                "teamGroupXtdPool": _round(row["team_group_xtd_pool_prior"], 2),
                "vacatedShareGained": _round(row["vacated_opportunity_share_gained"], 3),
                "stolenShareLost": _round(row["stolen_opportunity_share_lost"], 3),
                "netShareChange": _round(row["net_opportunity_share_change"], 3),
                "opportunitySignal": _round(row["regression_signal_opportunity"], 2),
                "combinedSignal": _round(row["combined_signal"], 2),
                "projectedTd": _round(row["projected_td_next_season"], 2),
                "label": row["regression_label"],
                "vegas": (
                    {
                        "line": _round(v["vegas_td_line"], 1),
                        "market": v["vegas_market"],
                        "diff": _round(v["vegas_diff"], 2),
                    }
                    if v
                    else None
                ),
            }
        )
    players.sort(key=lambda p: p["combinedSignal"], reverse=True)
    return players


def build_meta(players: list[dict]) -> dict:
    labels = {}
    for p in players:
        labels[p["label"]] = labels.get(p["label"], 0) + 1
    matched_vegas = sum(1 for p in players if p["vegas"] is not None)
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "seasonPrior": config.PRIOR_SEASON,
        "seasonNext": config.NEXT_SEASON,
        "playerCount": len(players),
        "labelCounts": labels,
        "vegasMatchedCount": matched_vegas,
        "histSeasons": [config.HIST_SEASONS[0], config.HIST_SEASONS[-1]],
        "minOpportunities": config.MIN_OPPORTUNITIES,
    }


def main():
    players = build_players_payload()
    meta = build_meta(players)

    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (WEB_DATA_DIR / "players.json").write_text(json.dumps(players, indent=2))
    (WEB_DATA_DIR / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"Wrote {len(players)} players to {WEB_DATA_DIR / 'players.json'}")


if __name__ == "__main__":
    main()
