"""Leak-free match features built by replaying history in date order.

:class:`FeatureBuilder` keeps a running state for every team (recent results,
exponentially weighted averages, season totals, Elo rating, head-to-head
record). For each match it first *reads* the state to produce features and
only then *updates* the state with the result. A row's features therefore only
ever depend on matches played strictly before it, which is what makes the
backtests honest.

Feature groups (``h_`` = home team, ``a_`` = away team, ``d_`` = home minus away):

* rating:   Elo before kick-off and the Elo gap including home advantage
* form:     points per game, goals for/against over the last 3, 5 and 10 games
* venue:    home team's recent *home* form and away team's recent *away* form
* ewm:      exponentially weighted goals, shots and shots on target, for/against
* season:   points per game and goal difference per game so far this season
* schedule: days since previous match, matches already played in the season
* h2h:      average goal difference and home win rate in recent meetings
* market:   bookmaker probabilities with the margin removed (optional)
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .data import implied_probabilities
from .elo import EloRatings

FORM_WINDOWS = (3, 5, 10)
VENUE_WINDOW = 5
H2H_WINDOW = 6
MAX_REST_DAYS = 21


@dataclass
class _TeamState:
    recent: deque = field(default_factory=lambda: deque(maxlen=max(FORM_WINDOWS)))
    home_recent: deque = field(default_factory=lambda: deque(maxlen=VENUE_WINDOW))
    away_recent: deque = field(default_factory=lambda: deque(maxlen=VENUE_WINDOW))
    ewm: dict = field(default_factory=dict)
    last_date: pd.Timestamp | None = None
    season: str | None = None
    season_games: int = 0
    season_points: int = 0
    season_gd: int = 0
    total_games: int = 0


def _points(gf: float, ga: float) -> int:
    return 3 if gf > ga else 1 if gf == ga else 0


def _mean(seq, key):
    vals = [m[key] for m in seq]
    return float(np.mean(vals)) if vals else np.nan


class FeatureBuilder:
    def __init__(self, elo: EloRatings | None = None, ewm_alpha: float = 0.15, use_market: bool = True):
        self.elo = elo or EloRatings()
        self.alpha = ewm_alpha
        self.use_market = use_market
        self.teams: dict[str, _TeamState] = defaultdict(_TeamState)
        self.h2h: dict[tuple[str, str], deque] = defaultdict(lambda: deque(maxlen=H2H_WINDOW))

    # ---------------------------------------------------------------- read
    def _team_features(self, team: str, venue: str, date: pd.Timestamp, season: str) -> dict:
        s = self.teams[team]
        f = {}
        for n in FORM_WINDOWS:
            last = list(s.recent)[-n:]
            f[f"ppg{n}"] = _mean(last, "pts")
            f[f"gf{n}"] = _mean(last, "gf")
            f[f"ga{n}"] = _mean(last, "ga")
        venue_hist = s.home_recent if venue == "home" else s.away_recent
        f["venue_ppg"] = _mean(venue_hist, "pts")
        f["venue_gf"] = _mean(venue_hist, "gf")
        f["venue_ga"] = _mean(venue_hist, "ga")
        for k in ("gf", "ga", "sf", "sa", "sotf", "sota"):
            f[f"ewm_{k}"] = s.ewm.get(k, np.nan)
        # Shot quality proxy: goals per shot on target (finishing / goalkeeping luck).
        f["ewm_conv"] = f["ewm_gf"] / f["ewm_sotf"] if f["ewm_sotf"] and f["ewm_sotf"] > 0 else np.nan
        same_season = s.season == season
        g = s.season_games if same_season else 0
        f["season_games"] = g
        f["season_ppg"] = s.season_points / g if g else np.nan
        f["season_gdpg"] = s.season_gd / g if g else np.nan
        f["rest_days"] = (
            min((date - s.last_date).days, MAX_REST_DAYS) if s.last_date is not None else MAX_REST_DAYS
        )
        f["experience"] = min(s.total_games, 100)
        return f

    def features_for(self, home: str, away: str, date, season: str, odds=None, neutral: bool = False) -> dict:
        """Features for a (possibly future) fixture given the current state."""
        date = pd.Timestamp(date)
        self.elo.start_season(season)
        hf = self._team_features(home, "home", date, season)
        af = self._team_features(away, "away", date, season)
        out = {f"h_{k}": v for k, v in hf.items()}
        out.update({f"a_{k}": v for k, v in af.items()})
        for k in ("ppg5", "ppg10", "gf5", "ga5", "ewm_gf", "ewm_ga", "ewm_sf", "ewm_sa",
                  "ewm_sotf", "ewm_sota", "season_ppg", "season_gdpg", "rest_days"):
            out[f"d_{k}"] = hf[k] - af[k]
        out["h_elo"] = self.elo.rating(home)
        out["a_elo"] = self.elo.rating(away)
        out["elo_diff"] = self.elo.diff(home, away, neutral)
        out["elo_expected"] = self.elo.expected(home, away, neutral)
        # Expected-goal style composite: own attack vs opponent's defence.
        out["h_attack_vs_def"] = np.nanmean([hf["ewm_gf"], af["ewm_ga"]]) if not (
            np.isnan(hf["ewm_gf"]) and np.isnan(af["ewm_ga"])) else np.nan
        out["a_attack_vs_def"] = np.nanmean([af["ewm_gf"], hf["ewm_ga"]]) if not (
            np.isnan(af["ewm_gf"]) and np.isnan(hf["ewm_ga"])) else np.nan

        meetings = [m for m in self.h2h[tuple(sorted((home, away)))]]
        gd = [(m["gd"] if m["home"] == home else -m["gd"]) for m in meetings]
        out["h2h_n"] = len(gd)
        out["h2h_gd"] = float(np.mean(gd)) if gd else np.nan
        out["h2h_win_rate"] = float(np.mean([d > 0 for d in gd])) if gd else np.nan

        if self.use_market:
            if odds is not None and np.all(np.isfinite(odds)):
                p = implied_probabilities(np.asarray(odds, float)[None, :])[0]
            else:
                p = np.full(3, np.nan)
            out["mkt_home"], out["mkt_draw"], out["mkt_away"] = p
        return out

    # -------------------------------------------------------------- update
    def _update_team(self, team, date, season, venue, gf, ga, sf, sa, sotf, sota):
        s = self.teams[team]
        if s.season != season:
            s.season, s.season_games, s.season_points, s.season_gd = season, 0, 0, 0
        pts = _points(gf, ga)
        rec = {"pts": pts, "gf": gf, "ga": ga}
        s.recent.append(rec)
        (s.home_recent if venue == "home" else s.away_recent).append(rec)
        for k, v in (("gf", gf), ("ga", ga), ("sf", sf), ("sa", sa), ("sotf", sotf), ("sota", sota)):
            if v is None or not np.isfinite(v):
                continue
            old = s.ewm.get(k)
            s.ewm[k] = v if old is None else (1 - self.alpha) * old + self.alpha * v
        s.last_date = date
        s.season_games += 1
        s.season_points += pts
        s.season_gd += gf - ga
        s.total_games += 1

    def update(self, row) -> None:
        """Add one played match to the state."""
        hg, ag = float(row.home_goals), float(row.away_goals)
        self._update_team(row.home_team, row.date, row.season, "home", hg, ag,
                          row.home_shots, row.away_shots, row.home_sot, row.away_sot)
        self._update_team(row.away_team, row.date, row.season, "away", ag, hg,
                          row.away_shots, row.home_shots, row.away_sot, row.home_sot)
        self.h2h[tuple(sorted((row.home_team, row.away_team)))].append(
            {"home": row.home_team, "gd": hg - ag}
        )
        self.elo.start_season(row.season)
        self.elo.update(row.home_team, row.away_team, int(hg), int(ag))

    # --------------------------------------------------------------- batch
    def build(self, matches: pd.DataFrame) -> pd.DataFrame:
        """Features for every row of ``matches`` (must be date-sorted).

        Matches on the same date do not see each other's results. Unplayed
        rows get features but do not update the state.
        """
        rows: list[dict] = []
        pending: list = []
        current_date = None
        for r in matches.itertuples(index=False):
            if r.date != current_date:
                for p in pending:
                    self.update(p)
                pending, current_date = [], r.date
            odds = (r.odds_home, r.odds_draw, r.odds_away)
            rows.append(self.features_for(r.home_team, r.away_team, r.date, r.season, odds))
            if not (np.isnan(r.home_goals) or np.isnan(r.away_goals)):
                pending.append(r)
        for p in pending:
            self.update(p)
        return pd.DataFrame(rows, index=matches.index)


def build_features(matches: pd.DataFrame, use_market: bool = True, **kwargs) -> tuple[pd.DataFrame, FeatureBuilder]:
    """Convenience wrapper returning (features, builder-with-final-state)."""
    fb = FeatureBuilder(use_market=use_market, **kwargs)
    return fb.build(matches), fb
