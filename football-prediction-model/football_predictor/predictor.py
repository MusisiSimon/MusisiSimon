"""High-level predictor that ties every model together.

Components
----------
``dixon_coles``  time-weighted bivariate Poisson goal model
``elo``          Elo rating gap -> ordered logit
``ml``           classifier on ~70 engineered form/rating/schedule features
``market``       (optional) bookmaker probabilities with margin removed

The ensemble weights are learned from genuinely out-of-sample forecasts: a
walk-forward run over the most recent part of the history. All goal markets
come from the Dixon-Coles score matrix, rescaled so its 1X2 split matches the
ensemble, which keeps every market consistent with the headline probabilities.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .data import _infer_season, implied_probabilities, outcome, parse_dates, played
from .dixon_coles import DixonColesModel
from .elo import EloRatings, OrderedLogit
from .ensemble import Ensemble
from .features import FeatureBuilder
from .markets import fair_odds, market_sheet, rescale_to_1x2
from .ml_model import MLOutcomeModel

OUTCOMES = ("home", "draw", "away")
MARKET_COLS = ("mkt_home", "mkt_draw", "mkt_away")


@dataclass
class PredictorConfig:
    # Dixon-Coles
    dc_xi: float = 0.0019
    dc_l2: float = 0.5
    # Elo
    elo_k: float = 20.0
    elo_home_advantage: float = 65.0
    elo_season_regression: float = 0.25
    # ML
    ml_kind: str = "logistic"
    ml_recency_halflife_days: float | None = 540.0
    ml_C: float = 0.05
    use_market_features: bool = False  # feed bookmaker probabilities to the ML model
    min_history: int = 5  # games a team must have played before its rows train the ML model
    # Ensemble
    components: tuple[str, ...] = ("dixon_coles", "elo", "ml")
    include_market_component: bool = False
    ensemble_method: str = "linear"
    ensemble_shrinkage: float = 0.1
    ensemble_min_obs: int = 250
    ensemble_holdout_days: int = 365
    refit_every_days: int = 14
    ml_refit_every_days: int = 28  # the ML model changes slowly and is the costliest to refit

    def active_components(self) -> list[str]:
        comps = list(self.components)
        if self.include_market_component and "market" not in comps:
            comps.append("market")
        return comps


class FootballPredictor:
    def __init__(self, config: PredictorConfig | None = None):
        self.config = config or PredictorConfig()
        c = self.config
        self.dc = DixonColesModel(xi=c.dc_xi, l2=c.dc_l2)
        self.elo_logit = OrderedLogit()
        self.ml = MLOutcomeModel(kind=c.ml_kind, recency_halflife_days=c.ml_recency_halflife_days, C=c.ml_C)
        self.ensemble = Ensemble(method=c.ensemble_method, shrinkage=c.ensemble_shrinkage)
        self.builder_: FeatureBuilder | None = None
        self.matches_: pd.DataFrame | None = None
        self.features_: pd.DataFrame | None = None
        self.holdout_: pd.DataFrame | None = None

    # ---------------------------------------------------------- internals
    def new_builder(self) -> FeatureBuilder:
        c = self.config
        elo = EloRatings(k=c.elo_k, home_advantage=c.elo_home_advantage, season_regression=c.elo_season_regression)
        return FeatureBuilder(elo=elo, use_market=True)

    def ml_columns(self, features: pd.DataFrame) -> list[str]:
        cols = list(features.columns)
        if not self.config.use_market_features:
            cols = [c for c in cols if c not in MARKET_COLS]
        return cols

    def fit_components(self, matches: pd.DataFrame, features: pd.DataFrame, as_of, fit_ml: bool = True) -> None:
        """Fit every component on played matches dated on or before ``as_of``.

        ``fit_ml=False`` keeps the previously fitted ML model (used by the
        backtest to refit it less often than the cheap models)."""
        as_of = pd.Timestamp(as_of)
        hist = matches[(matches["date"] <= as_of)].dropna(subset=["home_goals", "away_goals"])
        comps = self.config.active_components()
        if "dixon_coles" in comps:
            self.dc.fit(hist, as_of=as_of)
        f = features.loc[hist.index]
        y = outcome(hist["home_goals"], hist["away_goals"])
        if "elo" in comps:
            self.elo_logit.fit(f["elo_diff"].to_numpy(), y)
        if "ml" in comps and (fit_ml or self.ml.model_ is None):
            mh = self.config.min_history
            ok = ((f["h_experience"] >= mh) & (f["a_experience"] >= mh)).to_numpy()
            self.ml.fit(f.loc[ok, self.ml_columns(features)], y[ok], dates=hist.loc[ok, "date"])

    def component_probs(self, fixtures: pd.DataFrame, features: pd.DataFrame) -> dict[str, np.ndarray]:
        out = {}
        comps = self.config.active_components()
        if "dixon_coles" in comps:
            out["dixon_coles"] = self.dc.predict_proba_frame(fixtures)
        if "elo" in comps:
            out["elo"] = self.elo_logit.predict_proba(features["elo_diff"].to_numpy())
        if "ml" in comps:
            out["ml"] = self.ml.predict_proba(features)
        if "market" in comps:
            out["market"] = features[list(MARKET_COLS)].to_numpy(float)
        return out

    # ----------------------------------------------------------------- API
    def fit(self, matches: pd.DataFrame, learn_weights: bool = True, verbose: bool = False) -> "FootballPredictor":
        """Fit on all played matches in ``matches``.

        With ``learn_weights`` the ensemble weights are estimated from a
        walk-forward over the last ``ensemble_holdout_days`` of data;
        otherwise components are averaged equally.
        """
        df = played(matches)
        self.builder_ = self.new_builder()
        self.features_ = self.builder_.build(df)
        self.matches_ = df
        names = self.config.active_components()

        holdout_start = df["date"].max() - pd.Timedelta(days=self.config.ensemble_holdout_days)
        enough = (df["date"] < holdout_start).sum() >= 300 and (df["date"] >= holdout_start).sum() >= 100
        if learn_weights and enough and len(names) > 1:
            from .backtest import walk_forward

            bt = walk_forward(df, self.config, test_start=holdout_start, features=self.features_,
                              refit_every_days=max(self.config.refit_every_days, 28), verbose=verbose)
            self.holdout_ = bt.predictions
            comps = {n: bt.probs(n) for n in names}
            self.ensemble.fit(comps, bt.predictions["outcome"].to_numpy())
        else:
            self.ensemble.set_equal(names)

        self.fit_components(df, self.features_, df["date"].max())
        return self

    def _fixture_features(self, fixtures: pd.DataFrame) -> pd.DataFrame:
        # Work on a copy so predicting never mutates the fitted state
        # (e.g. starting a new Elo season for a fixture next season).
        builder = copy.deepcopy(self.builder_)
        rows = []
        for r in fixtures.itertuples(index=False):
            odds = tuple(getattr(r, k, np.nan) for k in ("odds_home", "odds_draw", "odds_away"))
            rows.append(builder.features_for(r.home_team, r.away_team, r.date, r.season, odds))
        return pd.DataFrame(rows, index=fixtures.index)

    @staticmethod
    def _prepare_fixtures(fixtures: pd.DataFrame, default_date) -> pd.DataFrame:
        fx = fixtures.copy()
        if "date" not in fx:
            fx["date"] = default_date
        fx["date"] = parse_dates(fx["date"])
        if "season" not in fx or fx["season"].isna().any():
            fx["season"] = _infer_season(fx["date"])
        for c in ("odds_home", "odds_draw", "odds_away"):
            if c not in fx:
                fx[c] = np.nan
        return fx

    def predict(self, fixtures: pd.DataFrame) -> pd.DataFrame:
        """1X2 probabilities from every component plus the ensemble.

        ``fixtures`` needs ``home_team`` and ``away_team``; ``date`` and odds
        columns are optional.
        """
        if self.builder_ is None:
            raise RuntimeError("call fit() first")
        default_date = self.matches_["date"].max() + pd.Timedelta(days=1)
        fx = self._prepare_fixtures(fixtures, default_date)
        feats = self._fixture_features(fx)
        comps = self.component_probs(fx, feats)
        ens = self.ensemble.predict_proba(comps)
        out = fx[["date", "home_team", "away_team"]].copy()
        for name, p in {**comps, "ensemble": ens}.items():
            for j, o in enumerate(OUTCOMES):
                out[f"{name}_{o}"] = p[:, j]
        xg = [self.dc.expected_goals(h, a) for h, a in zip(fx["home_team"], fx["away_team"])]
        out["xg_home"], out["xg_away"] = zip(*xg) if xg else ([], [])
        out["prediction"] = np.array(["Home win", "Draw", "Away win"])[ens.argmax(axis=1)]
        return out

    def predict_match(self, home: str, away: str, date=None, odds=None, neutral: bool = False) -> dict:
        """Full forecast for one fixture: probabilities, every goal market,
        fair odds and, if ``odds`` (home, draw, away) are given, the edge."""
        fx = pd.DataFrame([{"home_team": home, "away_team": away, "date": date}]).dropna(axis=1)
        if odds is not None:
            fx["odds_home"], fx["odds_draw"], fx["odds_away"] = odds
        row = self.predict(fx).iloc[0]
        ens = np.array([row[f"ensemble_{o}"] for o in OUTCOMES])
        m = rescale_to_1x2(self.dc.score_matrix(home, away, neutral), ens)
        sheet = market_sheet(m)
        components = {
            n: {o: float(row[f"{n}_{o}"]) for o in OUTCOMES}
            for n in self.config.active_components()
        }
        result = {
            "fixture": f"{home} vs {away}",
            "date": str(row["date"].date()),
            "probabilities": {o: float(p) for o, p in zip(OUTCOMES, ens)},
            "fair_odds": {o: round(fair_odds(p), 2) for o, p in zip(OUTCOMES, ens)},
            "prediction": row["prediction"],
            "components": components,
            "ensemble_weights": {k: float(v) for k, v in self.ensemble.weights_.items()},
            "ratings": self._ratings_snapshot(home, away),
            "markets": sheet,
            "unknown_teams": [t for t in (home, away) if t not in self.dc.attack_],
        }
        if odds is not None:
            mk = implied_probabilities(np.asarray(odds, float)[None, :])[0]
            result["value"] = {
                o: {
                    "odds": float(od),
                    "market_prob": float(mp),
                    "model_prob": float(p),
                    "edge": float(p * od - 1),
                }
                for o, od, mp, p in zip(OUTCOMES, odds, mk, ens)
            }
        return result

    def _ratings_snapshot(self, home: str, away: str) -> dict:
        elo = self.builder_.elo
        snap = {}
        for side, t in (("home", home), ("away", away)):
            a, d = self.dc._rating(t)
            snap[side] = {
                "team": t,
                "elo": float(elo.ratings.get(t, np.nan)),
                "dc_attack": float(a),
                "dc_defence": float(-d),
            }
        snap["dc_home_advantage"] = self.dc.home_adv_
        snap["dc_rho"] = self.dc.rho_
        return snap

    def describe(self) -> dict:
        return {"config": asdict(self.config), "ensemble_weights": self.ensemble.weights_}
