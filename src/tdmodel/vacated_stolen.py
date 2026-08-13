"""Proportional redistribution of vacated (departed teammate) and stolen
(newly added teammate) opportunity share to remaining same-team incumbents,
per team + position group.
"""

import polars as pl

from tdmodel.config import DEFAULT_ROOKIE_TIER, INCOMING_VETERAN_SHARE_CAP, ROOKIE_ROUND_TIERS
from tdmodel.roster_transitions import draft_round_tier


def compute_vacated_totals(departed: pl.DataFrame, shares_prior: pl.DataFrame) -> pl.DataFrame:
    """total_vacated_share per (team, position_group): sum of departed
    players' share of their prior team's group xTD pool.
    """
    dep_shares = departed.join(
        shares_prior.select(["player_id", "share"]), on="player_id", how="left"
    ).with_columns(pl.col("share").fill_null(0.0))
    return dep_shares.group_by(["team", "position_group"]).agg(
        pl.col("share").sum().alias("total_vacated_share")
    )


def filter_meaningful_additions(
    added: pl.DataFrame, shares_prior: pl.DataFrame, draft_picks_next: pl.DataFrame
) -> pl.DataFrame:
    """Restricts the raw "added" roster diff to players who plausibly compete
    for real opportunity share: actual draft picks, or veterans who had
    nonzero production (share > 0) on their prior team. Without this filter,
    "added" includes every UDFA/camp-body tryout player currently on an
    offseason 90-man roster (real 53-man competition is zero-sum, but a
    90-man roster stacks many more bodies per position than will ever play),
    which inflates the incoming-share total far beyond what any team's actual
    game-day rotation could absorb.
    """
    drafted_ids = set(draft_picks_next["gsis_id"].to_list())
    productive_veteran_ids = set(
        shares_prior.filter(pl.col("share") > 0)["player_id"].to_list()
    )
    keep_ids = drafted_ids | productive_veteran_ids
    return added.filter(pl.col("player_id").is_in(keep_ids))


def compute_incoming_shares(
    added: pl.DataFrame,
    shares_prior: pl.DataFrame,
    draft_picks_next: pl.DataFrame,
    rookie_lookup: pl.DataFrame,
    veteran_cap: float = INCOMING_VETERAN_SHARE_CAP,
) -> pl.DataFrame:
    """Estimated incoming_share per added player:
    - veteran (was on some other team's group roster last season): their own
      prior-team share, capped at veteran_cap.
    - rookie/newcomer (wasn't rostered anywhere last season): the empirical
      average share for their draft-round tier + position group.
    """
    prior_share_by_player = shares_prior.select(["player_id", "share"]).rename(
        {"share": "veteran_prior_share"}
    )
    added = added.join(prior_share_by_player, on="player_id", how="left")

    dp = (
        draft_picks_next.select(["gsis_id", "round"])
        .rename({"gsis_id": "player_id"})
        .unique(subset=["player_id"], keep="first")
    )
    added = added.join(dp, on="player_id", how="left")

    is_veteran = added["veteran_prior_share"].is_not_null()
    veteran_share = added["veteran_prior_share"].fill_null(0.0).clip(0.0, veteran_cap)

    tiers = [draft_round_tier(r) for r in added["round"].to_list()]
    rookie_frame = pl.DataFrame({"position_group": added["position_group"], "tier": tiers})
    rookie_share = rookie_frame.join(
        rookie_lookup.select(["tier", "position_group", "expected_incoming_share"]),
        on=["tier", "position_group"],
        how="left",
    )["expected_incoming_share"].fill_null(0.0)

    incoming_share = pl.Series(
        "incoming_share",
        [v if is_v else r for is_v, v, r in zip(is_veteran, veteran_share, rookie_share)],
    )

    return added.with_columns(incoming_share, pl.Series("is_veteran_addition", is_veteran))


def compute_stolen_totals(incoming_shares: pl.DataFrame) -> pl.DataFrame:
    return incoming_shares.group_by(["team", "position_group"]).agg(
        pl.col("incoming_share").sum().alias("total_incoming_share")
    )


def redistribute_to_incumbents(
    shares_prior: pl.DataFrame,
    same_team_player_ids: set[str],
    vacated_totals: pl.DataFrame,
    stolen_totals: pl.DataFrame,
) -> pl.DataFrame:
    """For each incumbent (same-team player), redistribute their team+group's
    total vacated/incoming share proportionally to their existing share
    within the group. If no incumbents remain in a team+group, that
    team+group's totals go unredistributed (flagged via zero_incumbent_groups
    for manual review) rather than dividing by zero.
    """
    incumbents = shares_prior.filter(pl.col("player_id").is_in(same_team_player_ids))

    remaining_sum = incumbents.group_by(["team", "position_group"]).agg(
        pl.col("share").sum().alias("remaining_share_sum")
    )
    incumbents = incumbents.join(remaining_sum, on=["team", "position_group"])
    incumbents = incumbents.join(vacated_totals, on=["team", "position_group"], how="left")
    incumbents = incumbents.join(stolen_totals, on=["team", "position_group"], how="left")
    incumbents = incumbents.with_columns(
        [
            pl.col("total_vacated_share").fill_null(0.0),
            pl.col("total_incoming_share").fill_null(0.0),
        ]
    )

    incumbents = incumbents.with_columns(
        pl.when(pl.col("remaining_share_sum") > 0)
        .then(pl.col("share") / pl.col("remaining_share_sum"))
        .otherwise(0.0)
        .alias("redistribution_weight")
    )

    incumbents = incumbents.with_columns(
        [
            (pl.col("total_vacated_share") * pl.col("redistribution_weight")).alias(
                "vacated_opportunity_share_gained"
            ),
            (pl.col("total_incoming_share") * pl.col("redistribution_weight")).alias(
                "stolen_opportunity_share_lost"
            ),
        ]
    )
    incumbents = incumbents.with_columns(
        (
            pl.col("vacated_opportunity_share_gained") - pl.col("stolen_opportunity_share_lost")
        ).alias("net_opportunity_share_change")
    )
    return incumbents


def zero_incumbent_groups(shares_prior: pl.DataFrame, same_team_player_ids: set[str]) -> pl.DataFrame:
    """team+position_group pairs that exist in shares_prior but have no
    remaining same-team incumbent -- vacated/stolen totals for these groups
    are not redistributed anywhere and should be reviewed manually.
    """
    incumbents = shares_prior.filter(pl.col("player_id").is_in(same_team_player_ids))
    remaining_groups = incumbents.select(["team", "position_group"]).unique()
    all_groups = shares_prior.select(["team", "position_group"]).unique()
    return all_groups.join(remaining_groups, on=["team", "position_group"], how="anti")
