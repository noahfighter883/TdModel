"""Aggregates scored opportunities to per-player-season actual TD vs xTD totals."""

import polars as pl


def aggregate_player_season(scored_opportunities: pl.DataFrame, season: int) -> pl.DataFrame:
    """Groups by player_id only (not player_id + player_name): nflverse's
    play-by-play sometimes spells the same player's abbreviated name two
    different ways within a season (e.g. "M.Wilson" vs "Mi.Wilson" for the
    same gsis_id, to disambiguate from a teammate with the same initial in
    some weeks but not others). Grouping on name too would silently split one
    real player's opportunities into two rows.
    """
    return (
        scored_opportunities.filter(pl.col("season") == season)
        .group_by("player_id")
        .agg(
            pl.col("player_name").first().alias("player_name"),
            pl.len().alias("opportunities"),
            pl.col("touchdown").sum().alias("actual_td"),
            pl.col("xtd_value").sum().alias("xtd"),
        )
    )
