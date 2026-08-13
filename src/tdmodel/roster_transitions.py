"""Per-team, per-position-group roster diffs: departures, additions, each
player's share of their team's group xTD pool, and an empirical lookup table
for how much of a team's group xTD pool an incoming rookie tends to capture
in their rookie season (used by vacated_stolen.py to estimate rookie
additions' incoming opportunity share).
"""

import polars as pl

from tdmodel.config import DEFAULT_ROOKIE_TIER, ROOKIE_ROUND_TIERS


def team_group_shares(agg: pl.DataFrame, roster_pg: pl.DataFrame) -> pl.DataFrame:
    """roster_pg: rosters.position_group_roster(rosters, season) output.
    agg: player_aggregation.aggregate_player_season(scored, season) output.

    Returns roster_pg with each player's opportunities/actual_td/xtd (0 if they
    never touched the ball), their team+position_group's total xTD pool, and
    their share of that pool.
    """
    joined = roster_pg.join(
        agg.select(["player_id", "opportunities", "actual_td", "xtd"]), on="player_id", how="left"
    ).with_columns(
        [
            pl.col("opportunities").fill_null(0),
            pl.col("actual_td").fill_null(0),
            pl.col("xtd").fill_null(0.0),
        ]
    )
    pool = joined.group_by(["team", "position_group"]).agg(
        pl.col("xtd").sum().alias("team_group_xtd_pool")
    )
    joined = joined.join(pool, on=["team", "position_group"])
    return joined.with_columns(
        pl.when(pl.col("team_group_xtd_pool") > 0)
        .then(pl.col("xtd") / pl.col("team_group_xtd_pool"))
        .otherwise(0.0)
        .alias("share")
    )


def departures_and_additions(
    roster_prior: pl.DataFrame, roster_next: pl.DataFrame
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """roster_prior/roster_next: rosters.position_group_roster() output for
    two consecutive seasons.

    Departed: on roster_prior, not on the same team in roster_next (released,
    retired, traded away, or signed elsewhere).
    Added: on roster_next, not on the same team in roster_prior (drafted,
    signed via free agency, or acquired via trade).
    """
    departed = (
        roster_prior.join(
            roster_next.select(["player_id", "team"]).rename({"team": "team_next"}),
            on="player_id",
            how="left",
        )
        .filter((pl.col("team_next").is_null()) | (pl.col("team_next") != pl.col("team")))
        .drop("team_next")
    )

    added = (
        roster_next.join(
            roster_prior.select(["player_id", "team"]).rename({"team": "team_prior"}),
            on="player_id",
            how="left",
        )
        .filter((pl.col("team_prior").is_null()) | (pl.col("team_prior") != pl.col("team")))
        .drop("team_prior")
    )

    return departed, added


def draft_round_tier(round_: int | None) -> str:
    if round_ is None:
        return DEFAULT_ROOKIE_TIER
    return ROOKIE_ROUND_TIERS.get(round_, DEFAULT_ROOKIE_TIER)


def rookie_shares_for_season(
    agg: pl.DataFrame, roster_pg: pl.DataFrame, draft_picks: pl.DataFrame, season: int
) -> pl.DataFrame:
    """Each rookie's (players whose rookie_year == season) share of their
    team's group xTD pool that season, tagged with a draft-round tier.
    """
    shares = team_group_shares(agg, roster_pg)
    rookies = shares.filter(pl.col("rookie_year") == season)

    dp = (
        draft_picks.filter(pl.col("season") == season)
        .select(["gsis_id", "round"])
        .rename({"gsis_id": "player_id"})
        .unique(subset=["player_id"], keep="first")
    )
    rookies = rookies.join(dp, on="player_id", how="left")
    tiers = [draft_round_tier(r) for r in rookies["round"].to_list()]
    return rookies.with_columns(pl.Series("tier", tiers)).select(
        ["player_id", "position_group", "tier", "share"]
    )


def build_rookie_share_lookup(rookie_shares_by_season: list[pl.DataFrame]) -> pl.DataFrame:
    """Averages rookie share of team-group xTD pool across many historical
    seasons, bucketed by (draft-round tier, position group). Busts (0 share)
    are included in the average on purpose -- this is meant to represent the
    expected share of a random incoming rookie in that tier, not just the
    ones who panned out.
    """
    all_rookies = pl.concat(rookie_shares_by_season)
    return (
        all_rookies.group_by(["tier", "position_group"])
        .agg(pl.col("share").mean().alias("expected_incoming_share"), pl.len().alias("n"))
        .sort(["position_group", "tier"])
    )
