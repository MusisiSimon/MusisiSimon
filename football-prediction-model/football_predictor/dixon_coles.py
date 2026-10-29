"""Dixon-Coles goal model with exponential time weighting.

Model (Dixon & Coles, 1997, "Modelling Association Football Scores and
Inefficiencies in the Football Betting Market"):

    home goals X ~ Poisson(lambda),  lambda = exp(c + h + att[home] + def[away])
    away goals Y ~ Poisson(mu),      mu     = exp(c     + att[away] + def[home])
    P(X=x, Y=y)  = tau(x, y) * Pois(x; lambda) * Pois(y; mu)

``att`` is attacking strength, ``def`` is defensive *weakness* (higher means
the team concedes more), ``h`` is home advantage and ``tau`` corrects the four
low scores 0-0, 1-0, 0-1, 1-1 through the dependence parameter ``rho``.

Each match's log-likelihood is weighted by ``exp(-xi * age_in_days)`` so the
model tracks changes in form. Parameters are found by maximum likelihood with
an analytic gradient, which makes refitting fast enough for walk-forward
backtests. A small ridge penalty shrinks ratings of teams with few matches
toward the league average.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .markets import DEFAULT_MAX_GOALS, market_sheet, outcome_probs, score_matrix


@dataclass
class DixonColesModel:
    xi: float = 0.0019  # time decay per day (half-life ~ 365 days)
    l2: float = 0.5  # ridge penalty on attack/defence ratings
    max_goals: int = DEFAULT_MAX_GOALS
    promoted_prior: str = "weakest"  # how to rate unseen teams: "weakest" | "average"
    min_weight: float = 1e-3  # matches with smaller weight are dropped from the fit

    teams_: list[str] = field(default_factory=list, init=False)
    attack_: dict[str, float] = field(default_factory=dict, init=False)
    defence_: dict[str, float] = field(default_factory=dict, init=False)
    intercept_: float = field(default=0.0, init=False)
    home_adv_: float = field(default=0.0, init=False)
    rho_: float = field(default=0.0, init=False)
    fitted_at_: pd.Timestamp | None = field(default=None, init=False)
    converged_: bool = field(default=False, init=False)
    _x0: np.ndarray | None = field(default=None, init=False, repr=False)

    # ------------------------------------------------------------------ fit
    def fit(self, matches: pd.DataFrame, as_of: pd.Timestamp | None = None) -> "DixonColesModel":
        """Fit to played matches dated on or before ``as_of`` (default: last match)."""
        df = matches.dropna(subset=["home_goals", "away_goals"])
        as_of = pd.Timestamp(as_of) if as_of is not None else df["date"].max()
        df = df[df["date"] <= as_of]
        age = (as_of - df["date"]).dt.days.to_numpy(dtype=float)
        w = np.exp(-self.xi * age)
        keep = w >= self.min_weight
        df, w = df[keep], w[keep]
        if len(df) < 10:
            raise ValueError("need at least 10 played matches to fit Dixon-Coles")

        teams = sorted(set(df["home_team"]) | set(df["away_team"]))
        idx = {t: i for i, t in enumerate(teams)}
        hi = df["home_team"].map(idx).to_numpy()
        ai = df["away_team"].map(idx).to_numpy()
        x = df["home_goals"].to_numpy(dtype=float)
        y = df["away_goals"].to_numpy(dtype=float)
        n = len(teams)

        # Warm start from the previous fit when the team list is unchanged.
        if self._x0 is not None and teams == self.teams_:
            x0 = self._x0
        else:
            mean_goals = max((x.mean() + y.mean()) / 2, 0.1)
            x0 = np.concatenate([np.zeros(2 * n), [np.log(mean_goals), 0.2, -0.05]])

        bounds = [(None, None)] * (2 * n + 2) + [(-0.35, 0.35)]
        res = minimize(
            _neg_log_lik,
            x0,
            args=(hi, ai, x, y, w, n, self.l2),
            jac=True,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 2000},
        )
        p = res.x
        att = p[:n] - p[:n].mean()
        dfn = p[n : 2 * n] - p[n : 2 * n].mean()
        self.teams_ = teams
        self.attack_ = dict(zip(teams, att))
        self.defence_ = dict(zip(teams, dfn))
        self.intercept_, self.home_adv_, self.rho_ = float(p[2 * n]), float(p[2 * n + 1]), float(p[2 * n + 2])
        self.fitted_at_ = as_of
        self.converged_ = bool(res.success)
        self._x0 = p
        return self

    # -------------------------------------------------------------- ratings
    def _rating(self, team: str) -> tuple[float, float]:
        if team in self.attack_:
            return self.attack_[team], self.defence_[team]
        if self.promoted_prior == "average" or len(self.teams_) < 4:
            return 0.0, 0.0
        # Promoted / unseen teams: average of the three weakest sides.
        net = sorted(self.teams_, key=lambda t: self.attack_[t] - self.defence_[t])[:3]
        return (
            float(np.mean([self.attack_[t] for t in net])),
            float(np.mean([self.defence_[t] for t in net])),
        )

    def expected_goals(self, home: str, away: str, neutral: bool = False) -> tuple[float, float]:
        ah, dh = self._rating(home)
        aa, da = self._rating(away)
        h = 0.0 if neutral else self.home_adv_
        lam = np.exp(self.intercept_ + h + ah + da)
        mu = np.exp(self.intercept_ + aa + dh)
        return float(lam), float(mu)

    def score_matrix(self, home: str, away: str, neutral: bool = False) -> np.ndarray:
        lam, mu = self.expected_goals(home, away, neutral)
        return score_matrix(lam, mu, self.rho_, self.max_goals)

    def predict_proba(self, home: str, away: str, neutral: bool = False) -> np.ndarray:
        """[P(home), P(draw), P(away)]."""
        return outcome_probs(self.score_matrix(home, away, neutral))

    def predict_proba_frame(self, fixtures: pd.DataFrame) -> np.ndarray:
        return np.vstack([self.predict_proba(h, a) for h, a in zip(fixtures["home_team"], fixtures["away_team"])])

    def markets(self, home: str, away: str, neutral: bool = False) -> dict:
        return market_sheet(self.score_matrix(home, away, neutral))

    def ratings_table(self) -> pd.DataFrame:
        """Team ratings, sorted by overall strength (attack minus defensive weakness).

        ``exp_gf`` / ``exp_ga`` are the goals a team would score/concede per
        game against an average opponent at a neutral venue.
        """
        rows = []
        for t in self.teams_:
            a, d = self.attack_[t], self.defence_[t]
            rows.append(
                {
                    "team": t,
                    "attack": a,
                    "defence": -d,
                    "overall": a - d,
                    "exp_gf": np.exp(self.intercept_ + self.home_adv_ / 2 + a),
                    "exp_ga": np.exp(self.intercept_ + self.home_adv_ / 2 + d),
                }
            )
        out = pd.DataFrame(rows).sort_values("overall", ascending=False).reset_index(drop=True)
        out.index += 1
        return out


def _neg_log_lik(params, hi, ai, x, y, w, n, l2):
    """Weighted negative log-likelihood of Dixon-Coles and its gradient."""
    att_raw, def_raw = params[:n], params[n : 2 * n]
    c, h, rho = params[2 * n], params[2 * n + 1], params[2 * n + 2]
    # Centre ratings so they sum to zero (identifiability); the gradient of a
    # centred vector w.r.t. its raw form is (I - 11'/n), applied below.
    att = att_raw - att_raw.mean()
    dfn = def_raw - def_raw.mean()

    lam = np.exp(c + h + att[hi] + dfn[ai])
    mu = np.exp(c + att[ai] + dfn[hi])

    m00 = (x == 0) & (y == 0)
    m01 = (x == 0) & (y == 1)
    m10 = (x == 1) & (y == 0)
    m11 = (x == 1) & (y == 1)
    tau = np.ones_like(lam)
    tau[m00] = 1 - lam[m00] * mu[m00] * rho
    tau[m01] = 1 + lam[m01] * rho
    tau[m10] = 1 + mu[m10] * rho
    tau[m11] = 1 - rho
    tau = np.maximum(tau, 1e-10)

    ll = w * (np.log(tau) + x * np.log(lam) - lam + y * np.log(mu) - mu)
    nll = -ll.sum() + l2 * (att @ att + dfn @ dfn)

    # d log tau / d lambda, d mu, d rho
    dl = np.zeros_like(lam)
    dm = np.zeros_like(lam)
    dr = np.zeros_like(lam)
    dl[m00] = -mu[m00] * rho / tau[m00]
    dm[m00] = -lam[m00] * rho / tau[m00]
    dr[m00] = -lam[m00] * mu[m00] / tau[m00]
    dl[m01] = rho / tau[m01]
    dr[m01] = lam[m01] / tau[m01]
    dm[m10] = rho / tau[m10]
    dr[m10] = mu[m10] / tau[m10]
    dr[m11] = -1 / tau[m11]

    g_lam = w * (x - lam + lam * dl)  # d ll / d log(lambda)
    g_mu = w * (y - mu + mu * dm)  # d ll / d log(mu)

    g_att = np.bincount(hi, g_lam, n) + np.bincount(ai, g_mu, n)
    g_def = np.bincount(ai, g_lam, n) + np.bincount(hi, g_mu, n)
    g_att = -(g_att - g_att.mean()) + 2 * l2 * (att - att.mean())
    g_def = -(g_def - g_def.mean()) + 2 * l2 * (dfn - dfn.mean())
    grad = np.concatenate(
        [g_att, g_def, [-(g_lam.sum() + g_mu.sum()), -g_lam.sum(), -(w * dr).sum()]]
    )
    return nll, grad


def tune_time_decay(
    matches: pd.DataFrame,
    candidates=(0.0005, 0.001, 0.0015, 0.002, 0.003, 0.004),
    test_from: pd.Timestamp | None = None,
    refit_every_days: int = 28,
) -> pd.DataFrame:
    """Choose ``xi`` by out-of-sample log loss on a walk-forward split.

    For each candidate, the model is refitted every ``refit_every_days`` on all
    matches before the block and scored on the matches inside it.
    """
    from .evaluation import log_loss
    from .data import outcome

    df = matches.dropna(subset=["home_goals", "away_goals"]).reset_index(drop=True)
    if test_from is None:
        test_from = df["date"].quantile(0.7)
    test = df[df["date"] >= test_from]
    y = outcome(test["home_goals"], test["away_goals"])
    edges = pd.date_range(test_from, df["date"].max() + pd.Timedelta(days=1), freq=f"{refit_every_days}D")
    if len(edges) == 0 or edges[-1] <= df["date"].max():
        edges = edges.append(pd.DatetimeIndex([df["date"].max() + pd.Timedelta(days=1)]))
    results = []
    for xi in candidates:
        model = DixonColesModel(xi=xi)
        probs = []
        for start, end in zip(edges[:-1], edges[1:]):
            block = test[(test["date"] >= start) & (test["date"] < end)]
            if block.empty:
                continue
            model.fit(df, as_of=start - pd.Timedelta(days=1))
            probs.append(model.predict_proba_frame(block))
        results.append({"xi": xi, "log_loss": log_loss(y, np.vstack(probs))})
    return pd.DataFrame(results).sort_values("log_loss").reset_index(drop=True)
