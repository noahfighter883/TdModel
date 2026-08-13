"""Fetches raw nflverse data via nflreadpy and caches pruned Parquet snapshots locally.

Two caching layers:
1. nflreadpy's own filesystem cache (survives across processes, keyed by URL).
2. Our own pruned Parquet snapshots under data/raw/, which decouple us from
   nflreadpy's cache eviction policy and give a frozen, reproducible input for
   a given pipeline run (important since 2026 roster/draft data changes daily
   during the offseason).
"""

import json
from datetime import datetime, timezone

import nflreadpy as nfl
import polars as pl

from tdmodel import config

nfl.config.update_config(
    cache_mode="filesystem",
    cache_dir=config.NFLREADPY_CACHE_DIR,
)

PBP_COLUMNS = [
    "season",
    "week",
    "game_id",
    "season_type",
    "posteam",
    "play_type",
    "yardline_100",
    "goal_to_go",
    "down",
    "two_point_attempt",
    "qb_kneel",
    "qb_spike",
    "rush_attempt",
    "pass_attempt",
    "complete_pass",
    "interception",
    "touchdown",
    "rush_touchdown",
    "pass_touchdown",
    "td_team",
    "receiver_player_id",
    "receiver_player_name",
    "rusher_player_id",
    "rusher_player_name",
]

MANIFEST_PATH = config.DATA_RAW / "_manifest.json"


def _record_manifest(name: str) -> None:
    config.DATA_RAW.mkdir(parents=True, exist_ok=True)
    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text())
    manifest[name] = datetime.now(timezone.utc).isoformat()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def _cached(name: str, force_refresh: bool, fetch_fn):
    path = config.DATA_RAW / f"{name}.parquet"
    if path.exists() and not force_refresh:
        return pl.read_parquet(path)
    df = fetch_fn()
    config.DATA_RAW.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
    _record_manifest(name)
    return df


def get_pbp(seasons=None, force_refresh: bool = False) -> pl.DataFrame:
    seasons = seasons or config.HIST_SEASONS

    def fetch():
        df = nfl.load_pbp(seasons)
        return df.select([c for c in PBP_COLUMNS if c in df.columns])

    return _cached("pbp", force_refresh, fetch)


def get_rosters(seasons=None, force_refresh: bool = False) -> pl.DataFrame:
    """Seasonal rosters (one row per player-season, reflecting their most
    recent team/status as of the latest available week). Used instead of
    load_rosters_weekly because nflreadpy does not yet serve weekly rosters
    for a season before it has started (e.g. 2026 during the offseason),
    while seasonal load_rosters already returns the current preseason
    snapshot for the upcoming season.
    """
    seasons = seasons or (config.HIST_SEASONS + [config.NEXT_SEASON])

    def fetch():
        return nfl.load_rosters(seasons)

    return _cached("rosters", force_refresh, fetch)


def get_player_stats(seasons=None, force_refresh: bool = False) -> pl.DataFrame:
    seasons = seasons or config.HIST_SEASONS

    def fetch():
        return nfl.load_player_stats(seasons, summary_level="reg")

    return _cached("player_stats", force_refresh, fetch)


def get_draft_picks(force_refresh: bool = False) -> pl.DataFrame:
    def fetch():
        return nfl.load_draft_picks(seasons=True)

    return _cached("draft_picks", force_refresh, fetch)


def get_teams(force_refresh: bool = False) -> pl.DataFrame:
    def fetch():
        return nfl.load_teams()

    return _cached("teams", force_refresh, fetch)


def refresh_all() -> None:
    get_pbp(force_refresh=True)
    get_rosters(force_refresh=True)
    get_player_stats(force_refresh=True)
    get_draft_picks(force_refresh=True)
    get_teams(force_refresh=True)


if __name__ == "__main__":
    import sys

    force = "--refresh-cache" in sys.argv
    print("Fetching pbp...")
    pbp = get_pbp(force_refresh=force)
    print(f"  {pbp.shape}")
    print("Fetching rosters...")
    rosters = get_rosters(force_refresh=force)
    print(f"  {rosters.shape}")
    print("Fetching player stats...")
    stats = get_player_stats(force_refresh=force)
    print(f"  {stats.shape}")
    print("Fetching draft picks...")
    picks = get_draft_picks(force_refresh=force)
    print(f"  {picks.shape}")
    print("Fetching teams...")
    teams = get_teams(force_refresh=force)
    print(f"  {teams.shape}")
