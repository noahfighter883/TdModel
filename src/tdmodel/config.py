"""Tunable constants for the touchdown regression pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_OUTPUT = ROOT / "data" / "output"
NFLREADPY_CACHE_DIR = ROOT / ".nflreadpy_cache"

# Baseline window for the xTD curve and player rate stats.
HIST_SEASONS = list(range(2016, 2026))

# The completed season being evaluated, and the season being projected into.
PRIOR_SEASON = 2025
NEXT_SEASON = 2026

# Position groups in scope. FB opportunities are folded into the RB group.
POSITION_GROUP_MAP = {
    "RB": "RB",
    "FB": "RB",
    "WR": "WR",
    "TE": "TE",
}
POSITION_GROUPS = ["RB", "WR", "TE"]

# Roster statuses that count as "on the team" for the same-team / roster-diff logic.
ROSTERED_STATUSES = {"ACT", "RES"}

# Team abbreviation quirks across nflverse data sources/seasons, normalized to
# the canonical abbreviation used by load_teams() (e.g. the 2026 preseason
# roster feed uses "AZ" for the Cardinals while every other season and
# load_teams() use "ARI").
TEAM_ABBR_ALIASES = {
    "AZ": "ARI",
    "OAK": "LV",
    "SD": "LAC",
    "STL": "LA",
    "LAR": "LA",
}

# Minimum opportunities (rush attempts + targets) in the prior season for a player
# to be included in the output.
MIN_OPPORTUNITIES = 30

# Cap on how much of their prior team's group-xTD share a veteran addition (via
# free agency or trade) is assumed to be able to replicate on the new team.
INCOMING_VETERAN_SHARE_CAP = 0.35

# Draft-round tiers used for the rookie incoming-share lookup table.
ROOKIE_ROUND_TIERS = {
    1: "round_1",
    2: "round_2_3",
    3: "round_2_3",
}
DEFAULT_ROOKIE_TIER = "round_4_7_udfa"

# yardline_100 bin edges (distance-to-end-zone) for the xTD curve, finest near
# the goal line where sample density and scoring-probability slope are both high.
YARDLINE_BIN_EDGES = list(range(0, 11, 1)) + list(range(12, 21, 2)) + list(range(25, 101, 5))
