import numpy as np
import polars as pl

from tdmodel.opportunities import ROLE_RUSH, ROLE_TARGET
from tdmodel.xtd_model import fit_curve, sanity_check_curve, score_opportunities

# Roughly realistic, monotonically decreasing touchdown rates by yardline,
# used to build a synthetic opportunities table with known ground truth.
RATES = {1: 0.7, 3: 0.55, 5: 0.4, 10: 0.25, 20: 0.12, 50: 0.03, 90: 0.005}
N_PER_YARDLINE = 200


def _make_opportunities(role: str) -> pl.DataFrame:
    rows = []
    for yardline, rate in RATES.items():
        n_td = round(rate * N_PER_YARDLINE)
        for i in range(N_PER_YARDLINE):
            rows.append(
                {
                    "season": 2025,
                    "week": 1,
                    "game_id": "g1",
                    "posteam": "AAA",
                    "yardline_100": yardline,
                    "role": role,
                    "player_id": f"P_{role}_{yardline}",
                    "player_name": "Synthetic Player",
                    "touchdown": 1 if i < n_td else 0,
                }
            )
    return pl.DataFrame(rows)


def synthetic_opportunities() -> pl.DataFrame:
    return pl.concat([_make_opportunities(ROLE_RUSH), _make_opportunities(ROLE_TARGET)])


def test_curve_is_monotonic_and_in_bounds():
    curve = fit_curve(synthetic_opportunities())
    assert sanity_check_curve(curve) == []


def test_curve_decreases_with_distance_from_goal():
    curve = fit_curve(synthetic_opportunities())
    for role in (ROLE_RUSH, ROLE_TARGET):
        role_curve = curve.filter(pl.col("role") == role).sort("yardline_100")
        p_yard_1 = role_curve.filter(pl.col("yardline_100") == 1)["p_td"][0]
        p_yard_50 = role_curve.filter(pl.col("yardline_100") == 50)["p_td"][0]
        p_yard_90 = role_curve.filter(pl.col("yardline_100") == 90)["p_td"][0]
        assert p_yard_1 > p_yard_50 > p_yard_90


def test_score_opportunities_joins_curve_probability():
    opps = synthetic_opportunities()
    curve = fit_curve(opps)
    scored = score_opportunities(opps, curve)

    assert scored["xtd_value"].is_null().sum() == 0
    assert scored["xtd_value"].min() >= 0
    assert scored["xtd_value"].max() <= 1

    # A player's total xTD across their opportunities should be a finite,
    # non-negative number consistent with the curve.
    totals = scored.group_by("player_id").agg(pl.col("xtd_value").sum().alias("xtd"))
    assert (totals["xtd"] >= 0).all()
    assert np.isfinite(totals["xtd"].to_numpy()).all()
