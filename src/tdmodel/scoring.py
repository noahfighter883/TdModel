"""Merges the efficiency signal (actual TD vs xTD) and the opportunity-shift
signal (vacated/stolen redistribution) into a final ranked regression table.
"""

import numpy as np
import polars as pl

from tdmodel.config import MIN_OPPORTUNITIES, NEXT_SEASON, PRIOR_SEASON

OUTPUT_COLUMNS = [
    "player_id",
    "player_name",
    "team",
    "position",
    "position_group",
    "season_prior",
    "season_next",
    "opportunities_prior",
    "actual_td_prior",
    "xtd_prior",
    "regression_signal_efficiency",
    "prior_group_share",
    "team_group_xtd_pool_prior",
    "vacated_opportunity_share_gained",
    "stolen_opportunity_share_lost",
    "net_opportunity_share_change",
    "regression_signal_opportunity",
    "combined_signal",
    "regression_label",
]


def _add_regression_label(df: pl.DataFrame) -> pl.DataFrame:
    values = df["combined_signal"].to_numpy()
    q10, q30, q70, q90 = np.quantile(values, [0.1, 0.3, 0.7, 0.9])

    def label(v: float) -> str:
        if v <= q10:
            return "Strong Negative (Sell)"
        if v <= q30:
            return "Negative"
        if v < q70:
            return "Neutral"
        if v < q90:
            return "Positive"
        return "Strong Positive (Buy)"

    return df.with_columns(pl.Series("regression_label", [label(v) for v in values]))


def build_scoring_table(
    redistributed: pl.DataFrame, min_opportunities: int = MIN_OPPORTUNITIES
) -> pl.DataFrame:
    """redistributed: vacated_stolen.redistribute_to_incumbents() output,
    already restricted to same-team incumbents.
    """
    df = redistributed.filter(pl.col("opportunities") >= min_opportunities)

    df = df.with_columns(
        [
            pl.lit(PRIOR_SEASON).alias("season_prior"),
            pl.lit(NEXT_SEASON).alias("season_next"),
            (pl.col("xtd") - pl.col("actual_td")).alias("regression_signal_efficiency"),
            (pl.col("net_opportunity_share_change") * pl.col("team_group_xtd_pool")).alias(
                "regression_signal_opportunity"
            ),
        ]
    )
    df = df.with_columns(
        (pl.col("regression_signal_efficiency") + pl.col("regression_signal_opportunity")).alias(
            "combined_signal"
        )
    )
    df = _add_regression_label(df)

    df = df.rename(
        {
            "full_name": "player_name",
            "opportunities": "opportunities_prior",
            "actual_td": "actual_td_prior",
            "xtd": "xtd_prior",
            "share": "prior_group_share",
            "team_group_xtd_pool": "team_group_xtd_pool_prior",
        }
    )
    return df.select(OUTPUT_COLUMNS).sort("combined_signal", descending=True)
