"""Scoring rules and diagnostics for 1X2 probability forecasts.

All functions take ``y`` encoded 0 = home win, 1 = draw, 2 = away win and
``p`` as an (n x 3) array of probabilities in the same order.

* **Log loss** - the negative mean log probability given to what happened.
  Strictly proper; punishes confident mistakes hard.
* **Brier score** - mean squared error of the probability vector.
* **Ranked probability score (RPS)** - Brier on the *cumulative*
  distribution. Because home/draw/away are ordered, predicting a draw when the
  home side wins is a smaller mistake than predicting an away win; RPS is the
  standard metric in the football forecasting literature (Constantinou &
  Fenton, 2012).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

EPS = 1e-12


def _check(y, p):
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) != len(y):
        raise ValueError("p must be (n, 3) and match len(y)")
    return y, p


def log_loss(y, p) -> float:
    y, p = _check(y, p)
    return float(-np.mean(np.log(np.clip(p[np.arange(len(y)), y], EPS, 1))))


def brier(y, p) -> float:
    y, p = _check(y, p)
    onehot = np.eye(3)[y]
    return float(np.mean(((p - onehot) ** 2).sum(axis=1)))


def rps(y, p) -> float:
    """Mean ranked probability score (lower is better, 0 is perfect)."""
    y, p = _check(y, p)
    onehot = np.eye(3)[y]
    cp, co = np.cumsum(p, axis=1)[:, :2], np.cumsum(onehot, axis=1)[:, :2]
    return float(np.mean(((cp - co) ** 2).sum(axis=1) / 2))


def accuracy(y, p) -> float:
    y, p = _check(y, p)
    return float(np.mean(p.argmax(axis=1) == y))


def score_all(y, p) -> dict[str, float]:
    return {
        "n": int(len(y)),
        "log_loss": log_loss(y, p),
        "brier": brier(y, p),
        "rps": rps(y, p),
        "accuracy": accuracy(y, p),
    }


def compare_models(y, predictions: dict[str, np.ndarray]) -> pd.DataFrame:
    """Score several models on the same matches; rows with NaN in any are dropped."""
    y = np.asarray(y)
    mask = np.ones(len(y), dtype=bool)
    for p in predictions.values():
        mask &= np.isfinite(p).all(axis=1)
    rows = [{"model": name, **score_all(y[mask], p[mask])} for name, p in predictions.items()]
    return pd.DataFrame(rows).set_index("model").sort_values("rps")


def calibration_table(y, p, n_bins: int = 10) -> pd.DataFrame:
    """Reliability table pooling all three outcomes.

    For each bin of forecast probability, compare the mean forecast with the
    observed frequency. A well calibrated model has ``forecast ~= observed``.
    """
    y, p = _check(y, p)
    onehot = np.eye(3)[y]
    probs, hits = p.ravel(), onehot.ravel()
    labels = np.tile(["home", "draw", "away"], len(y))
    bins = np.linspace(0, 1, n_bins + 1)
    idx = np.clip(np.digitize(probs, bins) - 1, 0, n_bins - 1)
    df = pd.DataFrame({"bin": idx, "p": probs, "hit": hits, "outcome": labels})
    out = (
        df.groupby("bin")
        .agg(n=("p", "size"), forecast=("p", "mean"), observed=("hit", "mean"))
        .reset_index()
    )
    out["range"] = [f"{bins[b]:.1f}-{bins[b + 1]:.1f}" for b in out["bin"]]
    # Standard error of the observed frequency, for judging gaps.
    out["std_err"] = np.sqrt(out["forecast"] * (1 - out["forecast"]) / out["n"])
    return out[["range", "n", "forecast", "observed", "std_err"]]


def expected_calibration_error(y, p, n_bins: int = 10) -> float:
    t = calibration_table(y, p, n_bins)
    return float((t["n"] * (t["forecast"] - t["observed"]).abs()).sum() / t["n"].sum())


def base_rate_forecast(y_train, n: int) -> np.ndarray:
    """Naive benchmark: always predict the historical outcome frequencies."""
    freq = np.bincount(np.asarray(y_train, dtype=int), minlength=3) / len(y_train)
    return np.tile(freq, (n, 1))
