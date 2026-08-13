"""Data-quality checks run as part of every pipeline execution."""

import polars as pl

from tdmodel.opportunities import ROLE_RUSH, ROLE_TARGET


def cross_check_opportunity_counts(
    opportunities: pl.DataFrame, player_stats: pl.DataFrame, season: int, tolerance: int = 5
) -> list[str]:
    """Compares our pbp-derived carries/targets per player for a season
    against nflreadpy's own load_player_stats aggregates. A small gap is
    expected (we deliberately exclude QB kneels and two-point attempts from
    "carries"); a gap beyond `tolerance` likely indicates a bug in the
    opportunity-extraction filtering logic.
    """
    ours = (
        opportunities.filter(pl.col("season") == season)
        .group_by(["player_id", "role"])
        .agg(pl.len().alias("n"))
        .pivot(on="role", index="player_id", values="n")
        .fill_null(0)
    )
    for role_col in (ROLE_RUSH, ROLE_TARGET):
        if role_col not in ours.columns:
            ours = ours.with_columns(pl.lit(0).alias(role_col))
    ours = ours.rename({ROLE_RUSH: "our_carries", ROLE_TARGET: "our_targets"})

    theirs = (
        player_stats.filter(pl.col("season") == season)
        .group_by("player_id")
        .agg(
            pl.col("carries").sum().alias("their_carries"),
            pl.col("targets").sum().alias("their_targets"),
        )
    )

    cmp = ours.join(theirs, on="player_id", how="inner").with_columns(
        [
            (pl.col("our_carries") - pl.col("their_carries")).abs().alias("carry_diff"),
            (pl.col("our_targets") - pl.col("their_targets")).abs().alias("target_diff"),
        ]
    )

    warnings = []
    bad_carries = cmp.filter(pl.col("carry_diff") > tolerance)
    bad_targets = cmp.filter(pl.col("target_diff") > tolerance)
    if bad_carries.height > 0:
        warnings.append(
            f"{bad_carries.height} players have carry counts differing from "
            f"load_player_stats by more than {tolerance}"
        )
    if bad_targets.height > 0:
        warnings.append(
            f"{bad_targets.height} players have target counts differing from "
            f"load_player_stats by more than {tolerance}"
        )
    return warnings
