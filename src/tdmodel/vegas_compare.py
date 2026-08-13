"""Matches manually-entered sportsbook season-long touchdown lines against
our model's projected 2026 touchdowns, to see where the regression signal
agrees or disagrees with the market.

Both our scoring table and the sportsbook lines use full player names, but
formatting still drifts (suffixes like "III"/"Jr.", punctuation, apostrophes),
so names are normalized to (first initial, alphanumeric-only full name minus
suffix) before matching, rather than relying on exact string equality.
"""

import re

import polars as pl

from tdmodel.config import TEAM_ABBR_ALIASES

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def _normalize_team(team: str) -> str:
    team = team.strip().upper()
    return TEAM_ABBR_ALIASES.get(team, team)


def _alnum(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


def _strip_suffix_tokens(tokens: list[str]) -> list[str]:
    tokens = list(tokens)
    while tokens and _alnum(tokens[-1]) in SUFFIXES:
        tokens.pop()
    return tokens


def name_match_key(full_name: str) -> tuple[str, str]:
    """(first_initial, full_alnum_without_suffix) for a full name, e.g.
    'Kenneth Walker III' -> ('k', 'kennethwalker').
    """
    tokens = _strip_suffix_tokens(full_name.split())
    first_initial = _alnum(tokens[0])[:1]
    full_alnum = _alnum("".join(tokens))
    return first_initial, full_alnum


def match_vegas_lines(
    scoring_table: pl.DataFrame, vegas_lines: pl.DataFrame
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Returns (matched, unmatched_vegas_rows).

    matched: one row per scoring_table player with exactly one vegas-line
    candidate (team + first initial match, and one full-name key is a
    substring of the other -- handles minor formatting drift without
    requiring exact equality), with vegas_td_line and vegas_diff
    (projected_td_next_season - vegas_td_line) appended. Players with zero or
    ambiguous (>1) candidates are left out of matched rather than guessed at.

    unmatched_vegas: vegas lines that never matched any scoring_table row
    (e.g. below MIN_OPPORTUNITIES last season, changed teams, or a genuine
    name-matching miss worth checking by hand).
    """
    vegas_rows = vegas_lines.to_dicts()
    for row in vegas_rows:
        fi, key = name_match_key(row["player_name"])
        row["_first_initial"] = fi
        row["_key"] = key
        row["_team_norm"] = _normalize_team(row["team"])

    matched_rows = []
    used_vegas_idx: set[int] = set()

    for srow in scoring_table.to_dicts():
        fi, key = name_match_key(srow["player_name"])
        team_norm = _normalize_team(srow["team"])
        candidates = [
            i
            for i, v in enumerate(vegas_rows)
            if v["_team_norm"] == team_norm
            and v["_first_initial"] == fi
            and (key in v["_key"] or v["_key"] in key)
        ]
        if len(candidates) == 1:
            idx = candidates[0]
            v = vegas_rows[idx]
            used_vegas_idx.add(idx)
            merged = dict(srow)
            merged["vegas_player_name"] = v["player_name"]
            merged["vegas_market"] = v["market"]
            merged["vegas_td_line"] = v["vegas_td_line"]
            merged["vegas_diff"] = merged["projected_td_next_season"] - v["vegas_td_line"]
            matched_rows.append(merged)

    unmatched_vegas = [
        {k: val for k, val in v.items() if not k.startswith("_")}
        for i, v in enumerate(vegas_rows)
        if i not in used_vegas_idx
    ]

    matched_df = pl.DataFrame(matched_rows) if matched_rows else pl.DataFrame()
    unmatched_df = pl.DataFrame(unmatched_vegas) if unmatched_vegas else pl.DataFrame()
    return matched_df, unmatched_df


if __name__ == "__main__":
    from tdmodel import config

    scoring_table = pl.read_csv(config.DATA_OUTPUT / f"td_regression_{config.NEXT_SEASON}.csv")
    vegas_lines = pl.read_csv(config.DATA_MANUAL / "vegas_td_lines_2026.csv")

    matched, unmatched = match_vegas_lines(scoring_table, vegas_lines)

    out_path = config.DATA_OUTPUT / "vegas_comparison_2026.csv"
    matched = matched.sort("vegas_diff", descending=True)
    matched.write_csv(out_path)

    print(f"Matched {matched.height}/{vegas_lines.height} vegas lines. Wrote {out_path}")
    if unmatched.height > 0:
        print(f"{unmatched.height} vegas lines did not match any scoring-table row:")
        print(unmatched.select(["player_name", "team", "vegas_td_line"]))
