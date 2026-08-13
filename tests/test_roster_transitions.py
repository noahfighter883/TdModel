import polars as pl
import pytest

from tdmodel.roster_transitions import departures_and_additions, team_group_shares
from tdmodel.vacated_stolen import (
    compute_vacated_totals,
    redistribute_to_incumbents,
    zero_incumbent_groups,
)


def test_team_group_shares_sum_to_one_when_pool_positive():
    agg = pl.DataFrame(
        {
            "player_id": ["A", "B", "C"],
            "player_name": ["A", "B", "C"],
            "opportunities": [10, 10, 10],
            "actual_td": [5, 3, 1],
            "xtd": [6.0, 3.0, 1.0],
        }
    )
    roster_pg = pl.DataFrame(
        {
            "player_id": ["A", "B", "C"],
            "full_name": ["A", "B", "C"],
            "team": ["T1", "T1", "T1"],
            "position": ["RB", "RB", "RB"],
            "position_group": ["RB", "RB", "RB"],
            "rookie_year": [2020, 2021, 2022],
        }
    )
    shares = team_group_shares(agg, roster_pg)
    assert shares["team_group_xtd_pool"].unique().to_list() == [10.0]
    got = dict(zip(shares["player_id"].to_list(), shares["share"].to_list()))
    assert got["A"] == pytest.approx(0.6)
    assert got["B"] == pytest.approx(0.3)
    assert got["C"] == pytest.approx(0.1)


def test_team_group_shares_zero_pool_gives_zero_share_not_error():
    agg = pl.DataFrame(
        {"player_id": [], "player_name": [], "opportunities": [], "actual_td": [], "xtd": []},
        schema={
            "player_id": pl.Utf8,
            "player_name": pl.Utf8,
            "opportunities": pl.Int64,
            "actual_td": pl.Int64,
            "xtd": pl.Float64,
        },
    )
    roster_pg = pl.DataFrame(
        {
            "player_id": ["E"],
            "full_name": ["E"],
            "team": ["T2"],
            "position": ["RB"],
            "position_group": ["RB"],
            "rookie_year": [2023],
        }
    )
    shares = team_group_shares(agg, roster_pg)
    assert shares["share"].to_list() == [0.0]
    assert shares["team_group_xtd_pool"].to_list() == [0.0]


def _roster_row(player_id, team, position_group="RB"):
    return {
        "player_id": player_id,
        "full_name": player_id,
        "team": team,
        "position": position_group,
        "position_group": position_group,
        "rookie_year": 2020,
    }


def test_departures_and_additions_classifies_moves_correctly():
    roster_prior = pl.DataFrame(
        [_roster_row("A", "T1"), _roster_row("B", "T1"), _roster_row("C", "T1")]
    )
    roster_next = pl.DataFrame(
        [_roster_row("A", "T1"), _roster_row("B", "T2"), _roster_row("D", "T1")]
    )

    departed, added = departures_and_additions(roster_prior, roster_next)

    assert set(departed["player_id"].to_list()) == {"B", "C"}
    assert set(departed.filter(pl.col("player_id") == "B")["team"]) == {"T1"}

    assert set(added["player_id"].to_list()) == {"B", "D"}
    assert set(added.filter(pl.col("player_id") == "B")["team"]) == {"T2"}
    assert set(added.filter(pl.col("player_id") == "D")["team"]) == {"T1"}


def test_redistribute_with_zero_incumbents_does_not_divide_by_zero():
    shares_prior = pl.DataFrame(
        {
            "player_id": ["X"],
            "team": ["T3"],
            "position_group": ["WR"],
            "share": [1.0],
        }
    )
    departed = pl.DataFrame({"player_id": ["X"], "team": ["T3"], "position_group": ["WR"]})
    vacated_totals = compute_vacated_totals(departed, shares_prior)
    stolen_totals = pl.DataFrame(
        {"team": [], "position_group": [], "total_incoming_share": []},
        schema={"team": pl.Utf8, "position_group": pl.Utf8, "total_incoming_share": pl.Float64},
    )

    same_team_ids: set[str] = set()  # X departed, nobody remains at T3/WR

    redistributed = redistribute_to_incumbents(
        shares_prior, same_team_ids, vacated_totals, stolen_totals
    )
    assert redistributed.height == 0

    zero_groups = zero_incumbent_groups(shares_prior, same_team_ids)
    assert zero_groups.to_dicts() == [{"team": "T3", "position_group": "WR"}]
