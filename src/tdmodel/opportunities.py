"""Converts play-by-play data into a table of touchdown-scoring "opportunities".

An opportunity is either:
- a rush attempt (excluding QB kneels), credited to rusher_player_id, or
- a pass target (including incompletions/interceptions), credited to
  receiver_player_id.

Two-point conversion plays are excluded: they always originate from a fixed
short yardline right after a score, face a defense that knows a run/pass is
coming, and would double-count scoring credit for the same possession if
included alongside the touchdown play that set them up.
"""

import polars as pl

ROLE_RUSH = "rush"
ROLE_TARGET = "target"


def build_opportunities(pbp: pl.DataFrame) -> pl.DataFrame:
    pbp = pbp.filter(
        (pl.col("season_type") == "REG") & (pl.col("two_point_attempt") != 1)
    )

    rush = (
        pbp.filter((pl.col("rush_attempt") == 1) & (pl.col("qb_kneel") != 1))
        .filter(pl.col("rusher_player_id").is_not_null())
        .select(
            [
                "season",
                "week",
                "game_id",
                "posteam",
                "yardline_100",
                pl.lit(ROLE_RUSH).alias("role"),
                pl.col("rusher_player_id").alias("player_id"),
                pl.col("rusher_player_name").alias("player_name"),
                pl.col("rush_touchdown").fill_null(0).cast(pl.Int8).alias("touchdown"),
            ]
        )
    )

    target = (
        pbp.filter(pl.col("pass_attempt") == 1)
        .filter(pl.col("receiver_player_id").is_not_null())
        .select(
            [
                "season",
                "week",
                "game_id",
                "posteam",
                "yardline_100",
                pl.lit(ROLE_TARGET).alias("role"),
                pl.col("receiver_player_id").alias("player_id"),
                pl.col("receiver_player_name").alias("player_name"),
                pl.col("pass_touchdown").fill_null(0).cast(pl.Int8).alias("touchdown"),
            ]
        )
    )

    return (
        pl.concat([rush, target])
        .filter(pl.col("yardline_100").is_not_null())
        .with_columns(pl.col("yardline_100").cast(pl.Int64))
    )
