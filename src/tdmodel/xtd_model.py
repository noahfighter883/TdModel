"""Fits P(touchdown | yardline_100, role) from historical opportunities and
scores opportunities against it to produce expected touchdowns (xTD).

Method: binned empirical touchdown rate (finer bins near the goal line),
smoothed with isotonic regression (monotonically non-increasing as distance
from the end zone grows) so the production curve is a directly-inspectable
lookup table rather than a black-box functional fit. This is preferred over a
raw logistic regression because it makes no assumption about the shape of the
curve and is trivially auditable ("at the 3-yard line, rushes have scored X%
of the time"); a logistic fit is used only as a secondary diagnostic, not in
production.
"""

import numpy as np
import polars as pl
from sklearn.isotonic import IsotonicRegression

from tdmodel.config import YARDLINE_BIN_EDGES
from tdmodel.opportunities import ROLE_RUSH, ROLE_TARGET

ROLES = [ROLE_RUSH, ROLE_TARGET]
MAX_YARDLINE = 99


def _bin_index(yardline_100: np.ndarray) -> np.ndarray:
    edges = np.array(YARDLINE_BIN_EDGES)
    # right-open bins: [edges[i], edges[i+1])
    return np.clip(np.digitize(yardline_100, edges, right=False) - 1, 0, len(edges) - 2)


def _bin_midpoint(bin_idx: np.ndarray) -> np.ndarray:
    edges = np.array(YARDLINE_BIN_EDGES)
    lo = edges[bin_idx]
    hi = edges[bin_idx + 1]
    return (lo + hi) / 2.0


def fit_curve(opportunities: pl.DataFrame) -> pl.DataFrame:
    """Returns a lookup table with one row per (role, yardline_100 0..99)
    and the smoothed touchdown probability p_td.
    """
    df = opportunities.with_columns(
        pl.col("yardline_100").map_batches(
            lambda s: pl.Series(_bin_index(s.to_numpy())), return_dtype=pl.Int64
        ).alias("bin_idx")
    )

    binned = (
        df.group_by(["role", "bin_idx"])
        .agg(
            pl.len().alias("opportunities"),
            pl.col("touchdown").sum().alias("tds"),
        )
        .with_columns((pl.col("tds") / pl.col("opportunities")).alias("raw_rate"))
        .sort(["role", "bin_idx"])
    )

    curves = []
    all_yardlines = np.arange(0, MAX_YARDLINE + 1)
    for role in ROLES:
        role_bins = binned.filter(pl.col("role") == role)
        bin_idx = role_bins["bin_idx"].to_numpy()
        midpoints = _bin_midpoint(bin_idx)
        raw_rate = role_bins["raw_rate"].to_numpy()
        weights = role_bins["opportunities"].to_numpy()

        iso = IsotonicRegression(increasing=False, out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso.fit(midpoints, raw_rate, sample_weight=weights)
        p_td = iso.predict(all_yardlines)

        curves.append(
            pl.DataFrame(
                {
                    "role": [role] * len(all_yardlines),
                    "yardline_100": all_yardlines,
                    "p_td": p_td,
                }
            )
        )

    return pl.concat(curves)


def score_opportunities(opportunities: pl.DataFrame, curve: pl.DataFrame) -> pl.DataFrame:
    return opportunities.join(curve, on=["role", "yardline_100"], how="left").rename(
        {"p_td": "xtd_value"}
    )


def sanity_check_curve(curve: pl.DataFrame) -> list[str]:
    """Returns a list of warning messages; empty list means the curve looks sane."""
    warnings = []
    for role in ROLES:
        role_curve = curve.filter(pl.col("role") == role).sort("yardline_100")
        p_td = role_curve["p_td"].to_numpy()

        if (p_td < 0).any() or (p_td > 1).any():
            warnings.append(f"{role}: p_td outside [0,1] range")

        diffs = np.diff(p_td)
        if (diffs > 1e-9).any():
            warnings.append(f"{role}: p_td is not monotonically non-increasing")

        one_yard_rate = role_curve.filter(pl.col("yardline_100") == 1)["p_td"][0]
        if not (0.2 <= one_yard_rate <= 0.9):
            warnings.append(
                f"{role}: implausible 1-yard-line score rate ({one_yard_rate:.2f})"
            )

    return warnings
