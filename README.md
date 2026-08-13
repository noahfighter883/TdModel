# TdModel — NFL Touchdown Regression Model

Identifies skill-position players (RB/WR/TE) who are due for positive or
negative touchdown regression next season, based on:

1. **Efficiency**: actual touchdowns vs. an expected-touchdowns (xTD) baseline
   built from each rush attempt / pass target's historical score probability
   at its exact yardline.
2. **Opportunity shift**: red-zone opportunity share likely gained from a
   departed same-position teammate ("vacated"), or lost to a newly added
   same-position teammate via free agency, trade, or the draft ("stolen").

Only players who stayed on the same team into next season are scored.

Data comes from the free, open-source [nflverse](https://github.com/nflverse)
ecosystem via `nflreadpy`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Running the pipeline

```bash
source .venv/bin/activate
python -m tdmodel.run_pipeline
```

Add `--refresh-cache` to force a re-download of raw nflverse data (otherwise
cached Parquet snapshots under `data/raw/` are reused). Output is written to
`data/output/td_regression_<next_season>.csv`.

Tunable constants (history window, position groups, thresholds) live in
[`src/tdmodel/config.py`](src/tdmodel/config.py).

## Pipeline

`ingest.py` → `opportunities.py` → `xtd_model.py` → `player_aggregation.py` +
`rosters.py` → `roster_transitions.py` + `vacated_stolen.py` → `scoring.py`,
orchestrated by `run_pipeline.py`. See module docstrings for each step's
methodology.

## Output columns

| Column | Meaning |
|---|---|
| `actual_td_prior` / `xtd_prior` | actual vs. expected touchdowns last season |
| `regression_signal_efficiency` | `xtd_prior - actual_td_prior` (positive = due for a bounce-back) |
| `net_opportunity_share_change` | projected change in the player's share of their team+position group's opportunity pool, from vacated/stolen redistribution |
| `regression_signal_opportunity` | that share change converted to xTD units |
| `combined_signal` | sum of the two signals above |
| `regression_label` | quantile-bucketed tier: Strong Negative (Sell) / Negative / Neutral / Positive / Strong Positive (Buy) |

## Documented assumptions (v1)

- FB folded into the RB position group.
- Two-point conversion plays and postseason plays excluded from opportunities and the xTD curve.
- Rookie incoming-share estimated from an empirical lookup table bucketed by draft-round tier (1 / 2–3 / 4–7+UDFA), not per-round.
- Veteran incoming-share = their own prior-team share, capped at `INCOMING_VETERAN_SHARE_CAP` (default 35%).
- The 90-man preseason roster (before final cuts) inflates the raw "added players" list with camp bodies; `filter_meaningful_additions` restricts incoming-share estimation to actual draft picks and veterans with nonzero prior production.
- Team abbreviations are normalized via `config.TEAM_ABBR_ALIASES` (e.g. the 2026 preseason roster feed uses `AZ` for Arizona while every other season and `load_teams()` use `ARI`) — check this mapping if a team's roster diff looks empty.
- Team-level position-group opportunity pool size is assumed constant year over year (no team pace/volume trend modeling in v1).
- `MIN_OPPORTUNITIES` (30) and `INCOMING_VETERAN_SHARE_CAP` (0.35) are reasonable defaults, not backtested.

## Manual spot-check checklist

Before trusting a run's output:
- [ ] `xtd_model.sanity_check_curve` and `qa.cross_check_opportunity_counts` printed no warnings (or only expected QB-kneel carry-count noise, since QBs are excluded from scoring anyway).
- [ ] Pick 2–3 well-known prior-season TD-variance storylines and confirm `regression_signal_efficiency` has the expected sign/magnitude.
- [ ] Pick 2–3 known offseason moves (a notable RB/WR free-agent signing, a notable retirement) and confirm they surface correctly in the roster-transition data for the right teams.
- [ ] Re-run closer to final roster cutdown for the freshest "same team" signal.

## Future roadmap (not built yet)

- Compare `combined_signal` / `regression_label` against Vegas player prop and season win-total touchdown lines.
- A dashboard on top of the output table.
