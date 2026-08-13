"""Roster helpers: position-group mapping and same-team detection.

Uses nflreadpy's seasonal `load_rosters` output (one row per player-season,
reflecting their most-recent team/status as of the latest available week for
that season) as the single source of truth for "which team was this player
on in season X" -- both for the same-team filter used in final scoring and
for the departure/addition detection in roster_transitions.py, so the two
stay consistent with each other.
"""

import polars as pl

from tdmodel.config import POSITION_GROUP_MAP, ROSTERED_STATUSES, TEAM_ABBR_ALIASES


def position_group_roster(rosters: pl.DataFrame, season: int) -> pl.DataFrame:
    """One row per rostered RB/FB/WR/TE player for a season, with position_group."""
    return (
        rosters.filter(pl.col("season") == season)
        .filter(pl.col("status").is_in(ROSTERED_STATUSES))
        .filter(pl.col("gsis_id").is_not_null() & (pl.col("gsis_id") != ""))
        .filter(pl.col("position").is_in(list(POSITION_GROUP_MAP.keys())))
        .with_columns(
            pl.col("position").replace(POSITION_GROUP_MAP).alias("position_group"),
            pl.col("team").replace(TEAM_ABBR_ALIASES).alias("team"),
        )
        .select(["gsis_id", "full_name", "team", "position", "position_group", "rookie_year"])
        .unique(subset=["gsis_id"], keep="first")
        .rename({"gsis_id": "player_id"})
    )


def same_team_table(rosters: pl.DataFrame, season_prior: int, season_next: int) -> pl.DataFrame:
    """One row per player rostered at RB/WR/TE in season_prior, with their
    season_prior team, season_next team (if still rostered at the position
    anywhere), and a same_team flag.
    """
    prior = position_group_roster(rosters, season_prior).rename({"team": "team_prior"})
    nxt = position_group_roster(rosters, season_next).select(["player_id", "team"]).rename(
        {"team": "team_next"}
    )
    joined = prior.join(nxt, on="player_id", how="left")
    return joined.with_columns(
        (pl.col("team_prior") == pl.col("team_next")).fill_null(False).alias("same_team")
    )
