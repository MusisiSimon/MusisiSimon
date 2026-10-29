"""Elo ratings for football and an ordered-logit map from rating gap to 1X2.

The rating update follows the World Football Elo scheme:

    R_new = R_old + K * G * (S - E),   E = 1 / (1 + 10 ** (-(dr) / 400))

where ``dr`` is the rating gap including home advantage, ``S`` is 1/0.5/0 for
win/draw/loss and ``G`` scales the update by the margin of victory. Ratings are
pulled toward the mean between seasons to reflect squad turnover.

Elo produces an *expected score*, not three outcome probabilities, so
:class:`OrderedLogit` learns how the rating gap maps to P(home/draw/away).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit


@dataclass
class EloRatings:
    k: float = 20.0
    home_advantage: float = 65.0
    initial: float = 1500.0
    season_regression: float = 0.25  # fraction pulled back to the mean each new season
    new_team_offset: float = -60.0  # promoted teams start below average
    use_margin: bool = True

    ratings: dict[str, float] = field(default_factory=dict)
    _season: str | None = field(default=None, repr=False)
    _n_seasons: int = field(default=0, repr=False)

    def rating(self, team: str) -> float:
        if team not in self.ratings:
            # Teams first seen after the opening season are promoted sides;
            # in the opening season everyone is new and starts level.
            promoted = self._n_seasons > 1 and self.ratings
            base = np.mean(list(self.ratings.values())) if self.ratings else self.initial
            self.ratings[team] = base + (self.new_team_offset if promoted else 0.0)
        return self.ratings[team]

    def diff(self, home: str, away: str, neutral: bool = False) -> float:
        """Home minus away rating, including home advantage."""
        return self.rating(home) - self.rating(away) + (0.0 if neutral else self.home_advantage)

    def expected(self, home: str, away: str, neutral: bool = False) -> float:
        return 1.0 / (1.0 + 10 ** (-self.diff(home, away, neutral) / 400))

    def start_season(self, season: str) -> None:
        if season == self._season:
            return
        if self._season is not None and self.ratings:
            mean = np.mean(list(self.ratings.values()))
            for t in self.ratings:
                self.ratings[t] = mean + (self.ratings[t] - mean) * (1 - self.season_regression)
        self._season = season
        self._n_seasons += 1

    @staticmethod
    def margin_multiplier(goal_diff: int) -> float:
        gd = abs(goal_diff)
        if gd <= 1:
            return 1.0
        if gd == 2:
            return 1.5
        return (11 + gd) / 8

    def update(self, home: str, away: str, home_goals: int, away_goals: int,
               season: str | None = None, neutral: bool = False) -> float:
        """Apply one result; returns the rating change for the home side."""
        if season is not None:
            self.start_season(season)
        e = self.expected(home, away, neutral)
        s = 1.0 if home_goals > away_goals else 0.5 if home_goals == away_goals else 0.0
        g = self.margin_multiplier(home_goals - away_goals) if self.use_margin else 1.0
        delta = self.k * g * (s - e)
        self.ratings[home] += delta
        self.ratings[away] -= delta
        return delta

    def table(self) -> pd.DataFrame:
        out = pd.Series(self.ratings, name="elo").sort_values(ascending=False).to_frame()
        out.index.name = "team"
        return out.reset_index()


@dataclass
class OrderedLogit:
    """P(outcome <= k) = sigmoid(c_k + beta . x) for outcomes home < draw < away.

    With ``x`` = home-minus-away strength, a larger ``x`` pushes probability
    toward a home win. Works with any number of features (``x`` may be 2-D).
    """

    l2: float = 1e-4
    coef_: np.ndarray | None = None
    cuts_: np.ndarray | None = None
    _mean: np.ndarray | None = None
    _scale: np.ndarray | None = None

    def _prep(self, x) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        return x[:, None] if x.ndim == 1 else x

    def fit(self, x, y, sample_weight=None) -> "OrderedLogit":
        x = self._prep(x)
        self._mean, self._scale = x.mean(axis=0), x.std(axis=0) + 1e-9
        z = (x - self._mean) / self._scale
        y = np.asarray(y, dtype=int)
        w = np.ones(len(y)) if sample_weight is None else np.asarray(sample_weight, float)
        d = z.shape[1]

        def nll(theta):
            beta, c1, log_gap = theta[:d], theta[d], theta[d + 1]
            c2 = c1 + np.exp(log_gap)
            p = self._probs(z, beta, c1, c2)
            ll = np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1))
            return -(w * ll).sum() / w.sum() + self.l2 * beta @ beta

        theta0 = np.concatenate([np.full(d, 0.5), [-0.4, np.log(1.0)]])
        res = minimize(nll, theta0, method="L-BFGS-B")
        self.coef_ = res.x[:d]
        self.cuts_ = np.array([res.x[d], res.x[d] + np.exp(res.x[d + 1])])
        return self

    @staticmethod
    def _probs(z, beta, c1, c2):
        eta = z @ beta
        p_home = expit(c1 + eta)
        p_home_or_draw = expit(c2 + eta)
        return np.column_stack([p_home, p_home_or_draw - p_home, 1 - p_home_or_draw])

    def predict_proba(self, x) -> np.ndarray:
        z = (self._prep(x) - self._mean) / self._scale
        return self._probs(z, self.coef_, *self.cuts_)


def elo_history(matches: pd.DataFrame, elo: EloRatings | None = None) -> tuple[pd.DataFrame, EloRatings]:
    """Run Elo through all played matches in date order.

    Returns per-match pre-game ratings (no look-ahead) and the final state.
    """
    elo = elo or EloRatings()
    rows = []
    for r in matches.itertuples(index=False):
        elo.start_season(r.season)
        rh, ra = elo.rating(r.home_team), elo.rating(r.away_team)
        rows.append({"elo_home": rh, "elo_away": ra, "elo_diff": rh - ra + elo.home_advantage})
        if not (np.isnan(r.home_goals) or np.isnan(r.away_goals)):
            elo.update(r.home_team, r.away_team, int(r.home_goals), int(r.away_goals))
    return pd.DataFrame(rows, index=matches.index), elo
