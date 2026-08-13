import polars as pl

from tdmodel.opportunities import ROLE_RUSH, ROLE_TARGET, build_opportunities

BASE = {
    "season": 2025,
    "week": 1,
    "game_id": "2025_01_AAA_BBB",
    "season_type": "REG",
    "posteam": "AAA",
    "goal_to_go": 1,
    "down": 1,
    "complete_pass": None,
    "interception": None,
    "receiver_player_id": None,
    "receiver_player_name": None,
    "rusher_player_id": None,
    "rusher_player_name": None,
    "touchdown": 0,
    "rush_touchdown": 0,
    "pass_touchdown": 0,
    "td_team": None,
}


def _row(**overrides):
    row = dict(BASE)
    row.update(overrides)
    return row


STRING_COLUMNS = {
    "receiver_player_id": pl.Utf8,
    "receiver_player_name": pl.Utf8,
    "rusher_player_id": pl.Utf8,
    "rusher_player_name": pl.Utf8,
    "td_team": pl.Utf8,
}


def _pbp(rows):
    return pl.DataFrame(rows, schema_overrides=STRING_COLUMNS)


def test_rush_touchdown_counted_as_rush_opportunity():
    pbp = _pbp(
        [
            _row(
                play_type="run",
                yardline_100=2,
                two_point_attempt=0,
                qb_kneel=0,
                qb_spike=0,
                rush_attempt=1,
                pass_attempt=0,
                rusher_player_id="P1",
                rusher_player_name="Runner",
                rush_touchdown=1,
                touchdown=1,
            )
        ]
    )
    opps = build_opportunities(pbp)
    assert opps.height == 1
    row = opps.row(0, named=True)
    assert row["role"] == ROLE_RUSH
    assert row["player_id"] == "P1"
    assert row["touchdown"] == 1
    assert row["yardline_100"] == 2


def test_qb_kneel_excluded():
    pbp = _pbp(
        [
            _row(
                play_type="run",
                yardline_100=50,
                two_point_attempt=0,
                qb_kneel=1,
                qb_spike=0,
                rush_attempt=1,
                pass_attempt=0,
                rusher_player_id="QB1",
                rusher_player_name="Kneeler",
            )
        ]
    )
    opps = build_opportunities(pbp)
    assert opps.height == 0


def test_two_point_attempt_excluded():
    pbp = _pbp(
        [
            _row(
                play_type="run",
                yardline_100=2,
                two_point_attempt=1,
                qb_kneel=0,
                qb_spike=0,
                rush_attempt=1,
                pass_attempt=0,
                rusher_player_id="P1",
                rusher_player_name="Runner",
                rush_touchdown=1,
                touchdown=1,
            )
        ]
    )
    opps = build_opportunities(pbp)
    assert opps.height == 0


def test_incomplete_target_counts_as_opportunity_with_no_touchdown():
    pbp = _pbp(
        [
            _row(
                play_type="pass",
                yardline_100=10,
                two_point_attempt=0,
                qb_kneel=0,
                qb_spike=0,
                rush_attempt=0,
                pass_attempt=1,
                complete_pass=0,
                receiver_player_id="R1",
                receiver_player_name="Receiver",
            )
        ]
    )
    opps = build_opportunities(pbp)
    assert opps.height == 1
    row = opps.row(0, named=True)
    assert row["role"] == ROLE_TARGET
    assert row["touchdown"] == 0


def test_postseason_excluded():
    pbp = _pbp(
        [
            _row(
                season_type="POST",
                play_type="run",
                yardline_100=2,
                two_point_attempt=0,
                qb_kneel=0,
                qb_spike=0,
                rush_attempt=1,
                pass_attempt=0,
                rusher_player_id="P1",
                rusher_player_name="Runner",
                rush_touchdown=1,
                touchdown=1,
            )
        ]
    )
    opps = build_opportunities(pbp)
    assert opps.height == 0
