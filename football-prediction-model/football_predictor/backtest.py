"""Walk-forward backtesting and betting simulation.

The backtest mimics live use exactly: the test period is cut into blocks of
``refit_every_days``; before each block every model is refitted on matches
played strictly before the block starts, then forecasts the block. Ensemble
weights for a block are learned only from earlier blocks' out-of-sample
forecasts. Nothing the models see was unknown at the time.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import implied_probabilities, outcome, played
from .ensemble import Ensemble
from .evaluation import base_rate_forecast, calibration_table, compare_models
from .predictor import OUTCOMES, FootballPredictor, PredictorConfig


@dataclass
class BacktestResult:
    predictions: pd.DataFrame
    components: list[str]
    weights_history: pd.DataFrame

    def probs(self, name: str) -> np.ndarray:
        return self.predictions[[f"{name}_{o}" for o in OUTCOMES]].to_numpy(float)

    @property
    def models(self) -> list[str]:
        names = list(self.components) + ["ensemble", "base_rate"]
        if "market_home" in self.predictions and "market" not in names:
            names.append("market")
        return names

    def metrics(self, include_market: bool = True) -> pd.DataFrame:
        names = [n for n in self.models if include_market or n != "market"]
        y = self.predictions["outcome"].to_numpy()
        return compare_models(y, {n: self.probs(n) for n in names})

    def metrics_by_season(self, model: str = "ensemble") -> pd.DataFrame:
        rows = []
        for season, g in self.predictions.groupby("season"):
            m = compare_models(g["outcome"].to_numpy(), {model: g[[f"{model}_{o}" for o in OUTCOMES]].to_numpy()})
            rows.append({"season": season, **m.iloc[0].to_dict()})
        return pd.DataFrame(rows).set_index("season")

    def calibration(self, model: str = "ensemble", n_bins: int = 10) -> pd.DataFrame:
        return calibration_table(self.predictions["outcome"], self.probs(model), n_bins)

    def betting(self, model: str = "ensemble", **kwargs) -> "BettingResult":
        return simulate_betting(self.predictions, model, **kwargs)


def walk_forward(
    matches: pd.DataFrame,
    config: PredictorConfig | None = None,
    test_start=None,
    test_end=None,
    refit_every_days: int | None = None,
    features: pd.DataFrame | None = None,
    verbose: bool = False,
) -> BacktestResult:
    """Out-of-sample forecasts for every played match in [test_start, test_end].

    ``test_start`` defaults to the start of the second-to-last season so the
    models always have at least one full season of history.
    """
    config = config or PredictorConfig()
    df = played(matches)
    predictor = FootballPredictor(config)
    if features is None:
        features = predictor.new_builder().build(df)
    if test_start is None:
        seasons = sorted(df["season"].unique())
        test_start = df.loc[df["season"] == seasons[-2], "date"].min() if len(seasons) >= 3 else df["date"].quantile(0.5)
    test_start = pd.Timestamp(test_start)
    test_end = pd.Timestamp(test_end) if test_end is not None else df["date"].max()
    step = pd.Timedelta(days=refit_every_days or config.refit_every_days)

    names = config.active_components()
    ens = Ensemble(method=config.ensemble_method, shrinkage=config.ensemble_shrinkage)
    y_all = outcome(df["home_goals"], df["away_goals"])
    has_odds = df[["odds_home", "odds_draw", "odds_away"]].notna().all(axis=1).any()

    blocks, weight_rows = [], []
    oos_comps: dict[str, list[np.ndarray]] = {n: [] for n in names}
    oos_y: list[np.ndarray] = []
    ml_step = pd.Timedelta(days=max(config.ml_refit_every_days, step.days))
    last_ml_fit = None
    start = test_start
    while start <= test_end:
        end = start + step
        mask = ((df["date"] >= start) & (df["date"] < end) & (df["date"] <= test_end)).to_numpy()
        if mask.any():
            fit_ml = last_ml_fit is None or start - last_ml_fit >= ml_step
            predictor.fit_components(df, features, as_of=start - pd.Timedelta(days=1), fit_ml=fit_ml)
            if fit_ml:
                last_ml_fit = start
            block = df[mask]
            comps = predictor.component_probs(block, features[mask])

            n_oos = sum(len(v) for v in oos_y)
            if len(names) > 1 and n_oos >= config.ensemble_min_obs:
                ens.fit({k: np.vstack(v) for k, v in oos_comps.items()}, np.concatenate(oos_y))
            else:
                ens.set_equal(names)
            weight_rows.append({"block_start": start, "n_oos": n_oos, **ens.weights_})
            comps["ensemble"] = ens.predict_proba(comps)

            train_y = y_all[(df["date"] < start).to_numpy()]
            comps["base_rate"] = base_rate_forecast(train_y, mask.sum())
            if has_odds and "market" not in comps:
                comps["market"] = implied_probabilities(block[["odds_home", "odds_draw", "odds_away"]].to_numpy())

            out = block[["date", "season", "home_team", "away_team", "home_goals", "away_goals",
                         "odds_home", "odds_draw", "odds_away"]].copy()
            out["outcome"] = y_all[mask]
            for name, p in comps.items():
                for j, o in enumerate(OUTCOMES):
                    out[f"{name}_{o}"] = p[:, j]
            blocks.append(out)
            for k in names:
                oos_comps[k].append(comps[k])
            oos_y.append(y_all[mask])
            if verbose:
                print(f"  block {start.date()} .. {(end - pd.Timedelta(days=1)).date()}: {mask.sum():3d} matches")
        start = end

    if not blocks:
        raise ValueError("no played matches in the test window")
    return BacktestResult(pd.concat(blocks), names, pd.DataFrame(weight_rows))


# --------------------------------------------------------------------------- #
# Betting simulation
# --------------------------------------------------------------------------- #
@dataclass
class BettingResult:
    bets: pd.DataFrame
    summary: dict


def simulate_betting(
    predictions: pd.DataFrame,
    model: str = "ensemble",
    min_edge: float = 0.05,
    max_odds: float = 8.0,
    staking: str = "kelly",
    kelly_fraction: float = 0.25,
    max_stake_frac: float = 0.03,
    flat_stake: float = 1.0,
    bankroll: float = 100.0,
) -> BettingResult:
    """Bet on the outcome with the largest positive edge when it exceeds ``min_edge``.

    ``edge = model_prob * odds - 1``. Staking is either ``"flat"`` (fixed
    ``flat_stake`` units) or fractional ``"kelly"``: stake
    ``kelly_fraction * edge / (odds - 1)`` of the current bankroll, capped at
    ``max_stake_frac``. Matches on the same day are staked from the bankroll at
    the start of that day.

    This is an evaluation tool. A positive backtest on *synthetic* odds says
    nothing about real bookmakers, and even on real data past edge is a weak
    guide to future edge.
    """
    df = predictions.dropna(subset=["odds_home", "odds_draw", "odds_away"]).sort_values("date")
    p = df[[f"{model}_{o}" for o in OUTCOMES]].to_numpy(float)
    odds = df[["odds_home", "odds_draw", "odds_away"]].to_numpy(float)
    edge = p * odds - 1
    edge[odds > max_odds] = -np.inf
    pick = edge.argmax(axis=1)
    best = edge[np.arange(len(df)), pick]

    rows = []
    bank = bankroll
    for date, idx in df.groupby("date").indices.items():
        day_bank = bank
        for i in idx:
            if not best[i] > min_edge:
                continue
            o, k = odds[i, pick[i]], pick[i]
            if staking == "kelly":
                frac = min(kelly_fraction * best[i] / (o - 1), max_stake_frac)
                stake = frac * day_bank
            elif staking == "flat":
                stake = flat_stake
            else:
                raise ValueError("staking must be 'kelly' or 'flat'")
            won = df["outcome"].iat[i] == k
            pnl = stake * (o - 1) if won else -stake
            bank += pnl
            rows.append({
                "date": date,
                "match": f"{df['home_team'].iat[i]} v {df['away_team'].iat[i]}",
                "bet": OUTCOMES[k],
                "odds": o,
                "model_prob": p[i, k],
                "edge": best[i],
                "stake": stake,
                "won": bool(won),
                "pnl": pnl,
                "bankroll": bank,
            })
    bets = pd.DataFrame(rows)
    if bets.empty:
        return BettingResult(bets, {"n_bets": 0})
    curve = np.concatenate([[bankroll], bets["bankroll"].to_numpy()]) if staking == "kelly" else \
        bankroll + np.concatenate([[0], bets["pnl"].cumsum().to_numpy()])
    peak = np.maximum.accumulate(curve)
    summary = {
        "model": model,
        "staking": staking,
        "n_matches": int(len(df)),
        "n_bets": int(len(bets)),
        "hit_rate": float(bets["won"].mean()),
        "avg_odds": float(bets["odds"].mean()),
        "avg_edge": float(bets["edge"].mean()),
        "staked": float(bets["stake"].sum()),
        "profit": float(bets["pnl"].sum()),
        "roi": float(bets["pnl"].sum() / bets["stake"].sum()),
        "final_bankroll": float(curve[-1]),
        "max_drawdown": float(((peak - curve) / peak).max()),
        "bets_by_outcome": bets["bet"].value_counts().to_dict(),
    }
    return BettingResult(bets, summary)
