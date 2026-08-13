import polars as pl

from tdmodel.scoring import build_scoring_table


def _player(player_id, opportunities, actual_td, xtd, net_change=0.0, pool=10.0):
    return {
        "player_id": player_id,
        "full_name": player_id,
        "team": "T1",
        "position": "RB",
        "position_group": "RB",
        "opportunities": opportunities,
        "actual_td": actual_td,
        "xtd": xtd,
        "team_group_xtd_pool": pool,
        "share": xtd / pool if pool else 0.0,
        "net_opportunity_share_change": net_change,
        "vacated_opportunity_share_gained": max(net_change, 0.0),
        "stolen_opportunity_share_lost": max(-net_change, 0.0),
    }


def _redistributed(rows):
    return pl.DataFrame(rows)


def test_min_opportunities_filter_excludes_low_volume_players():
    df = _redistributed(
        [
            _player("A", opportunities=50, actual_td=5, xtd=5),
            _player("B", opportunities=5, actual_td=1, xtd=1),
        ]
    )
    table = build_scoring_table(df, min_opportunities=30)
    assert table["player_id"].to_list() == ["A"]


def test_combined_signal_formula():
    df = _redistributed(
        [_player("A", opportunities=50, actual_td=2, xtd=5, net_change=0.5, pool=10.0)]
    )
    table = build_scoring_table(df, min_opportunities=30)
    row = table.row(0, named=True)
    assert row["regression_signal_efficiency"] == 3.0  # xtd - actual_td
    assert row["regression_signal_opportunity"] == 5.0  # 0.5 * 10.0
    assert row["combined_signal"] == 8.0


def test_regression_label_extremes():
    rows = [
        _player(f"P{i}", opportunities=50, actual_td=10 - i, xtd=10)
        for i in range(10)  # combined_signal strictly increasing with i
    ]
    df = _redistributed(rows)
    table = build_scoring_table(df, min_opportunities=30)

    best = table.row(0, named=True)
    worst = table.row(table.height - 1, named=True)
    assert best["combined_signal"] > worst["combined_signal"]
    assert best["regression_label"] in {"Strong Positive (Buy)", "Positive"}
    assert worst["regression_label"] in {"Strong Negative (Sell)", "Negative"}
