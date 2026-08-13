"""End-to-end CLI: ingest -> opportunities -> xTD -> roster transitions ->
vacated/stolen redistribution -> final ranked touchdown regression table.

Usage:
    python -m tdmodel.run_pipeline [--refresh-cache]
"""

import argparse
import sys

import polars as pl

from tdmodel import config, ingest
from tdmodel.opportunities import build_opportunities
from tdmodel.player_aggregation import aggregate_player_season
from tdmodel.qa import cross_check_opportunity_counts
from tdmodel.roster_transitions import (
    build_rookie_share_lookup,
    departures_and_additions,
    rookie_shares_for_season,
    team_group_shares,
)
from tdmodel.rosters import position_group_roster, same_team_table
from tdmodel.scoring import build_scoring_table
from tdmodel.vacated_stolen import (
    compute_incoming_shares,
    compute_stolen_totals,
    compute_vacated_totals,
    filter_meaningful_additions,
    redistribute_to_incumbents,
    zero_incumbent_groups,
)
from tdmodel.xtd_model import fit_curve, sanity_check_curve, score_opportunities


def run(force_refresh: bool = False) -> pl.DataFrame:
    print("Loading raw data...")
    pbp = ingest.get_pbp(force_refresh=force_refresh)
    rosters = ingest.get_rosters(force_refresh=force_refresh)
    draft_picks = ingest.get_draft_picks(force_refresh=force_refresh)
    player_stats = ingest.get_player_stats(force_refresh=force_refresh)

    print("Building opportunities and xTD curve...")
    opportunities = build_opportunities(pbp)
    curve = fit_curve(opportunities)

    qa_warnings = cross_check_opportunity_counts(opportunities, player_stats, config.PRIOR_SEASON)
    if qa_warnings:
        print("Data-quality cross-check warnings:", file=sys.stderr)
        for w in qa_warnings:
            print(f"  - {w}", file=sys.stderr)

    curve_warnings = sanity_check_curve(curve)
    if curve_warnings:
        print("xTD curve sanity check warnings:", file=sys.stderr)
        for w in curve_warnings:
            print(f"  - {w}", file=sys.stderr)

    scored = score_opportunities(opportunities, curve)

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    curve.write_parquet(config.DATA_PROCESSED / "xtd_curve.parquet")

    print("Building rookie incoming-share lookup from historical seasons...")
    rookie_frames = [
        rookie_shares_for_season(
            aggregate_player_season(scored, season),
            position_group_roster(rosters, season),
            draft_picks,
            season,
        )
        for season in config.HIST_SEASONS
    ]
    rookie_lookup = build_rookie_share_lookup(rookie_frames)
    rookie_lookup.write_parquet(config.DATA_PROCESSED / "rookie_share_lookup.parquet")

    print(f"Computing {config.PRIOR_SEASON} team/position-group shares...")
    agg_prior = aggregate_player_season(scored, config.PRIOR_SEASON)
    roster_prior = position_group_roster(rosters, config.PRIOR_SEASON)
    roster_next = position_group_roster(rosters, config.NEXT_SEASON)
    shares_prior = team_group_shares(agg_prior, roster_prior)

    print("Detecting departures and additions...")
    departed, added_raw = departures_and_additions(roster_prior, roster_next)
    draft_picks_next = draft_picks.filter(pl.col("season") == config.NEXT_SEASON)
    added = filter_meaningful_additions(added_raw, shares_prior, draft_picks_next)

    vacated_totals = compute_vacated_totals(departed, shares_prior)
    incoming = compute_incoming_shares(added, shares_prior, draft_picks_next, rookie_lookup)
    stolen_totals = compute_stolen_totals(incoming)

    same_team = same_team_table(rosters, config.PRIOR_SEASON, config.NEXT_SEASON)
    same_team_ids = set(same_team.filter(pl.col("same_team"))["player_id"].to_list())

    zero_groups = zero_incumbent_groups(shares_prior, same_team_ids)
    if zero_groups.height > 0:
        print(
            f"Warning: {zero_groups.height} team/position-groups have no remaining "
            "same-team incumbent (vacated/stolen totals unredistributed):",
            file=sys.stderr,
        )
        print(zero_groups, file=sys.stderr)

    print("Redistributing vacated/stolen opportunity share...")
    redistributed = redistribute_to_incumbents(
        shares_prior, same_team_ids, vacated_totals, stolen_totals
    )

    print("Building final scoring table...")
    scoring_table = build_scoring_table(redistributed)

    config.DATA_OUTPUT.mkdir(parents=True, exist_ok=True)
    out_path = config.DATA_OUTPUT / f"td_regression_{config.NEXT_SEASON}.csv"
    scoring_table.write_csv(out_path)
    print(f"Wrote {scoring_table.height} rows to {out_path}")

    return scoring_table


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-cache", action="store_true")
    args = parser.parse_args()
    run(force_refresh=args.refresh_cache)
