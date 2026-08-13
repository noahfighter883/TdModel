"""Aggregates scored opportunities to per-player-season actual TD vs xTD totals."""

import polars as pl


def aggregate_player_season(scored_opportunities: pl.DataFrame, season: int) -> pl.DataFrame:
    return (
        scored_opportunities.filter(pl.col("season") == season)
        .group_by(["player_id", "player_name"])
        .agg(
            pl.len().alias("opportunities"),
            pl.col("touchdown").sum().alias("actual_td"),
            pl.col("xtd_value").sum().alias("xtd"),
        )
    )
