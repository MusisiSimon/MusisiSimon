"""Combine several probability forecasts into one.

Two pooling rules are supported:

* ``"linear"``      p = sum_k w_k * p_k
* ``"logarithmic"`` p proportional to prod_k p_k ** w_k (geometric pooling;
  sharper, and rewards models that agree)

Weights are non-negative and sum to one (softmax parametrisation) and are
chosen to minimise log loss on out-of-sample forecasts. Minimising on
in-sample forecasts would favour whichever model overfits most.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax

from .evaluation import log_loss


def pool(probs: list[np.ndarray], weights: np.ndarray, method: str = "linear") -> np.ndarray:
    stack = np.stack(probs)  # (k, n, 3)
    w = np.asarray(weights)[:, None, None]
    if method == "linear":
        out = (w * stack).sum(axis=0)
    elif method == "logarithmic":
        out = np.exp((w * np.log(np.clip(stack, 1e-12, 1))).sum(axis=0))
    else:
        raise ValueError("method must be 'linear' or 'logarithmic'")
    return out / out.sum(axis=1, keepdims=True)


@dataclass
class Ensemble:
    method: str = "linear"
    shrinkage: float = 0.1  # pull weights toward equal to reduce variance
    weights_: dict[str, float] = field(default_factory=dict)

    def fit(self, components: dict[str, np.ndarray], y) -> "Ensemble":
        names = list(components)
        y = np.asarray(y)
        mask = np.ones(len(y), dtype=bool)
        for p in components.values():
            mask &= np.isfinite(p).all(axis=1)
        probs = [components[n][mask] for n in names]
        ym = y[mask]

        def objective(z):
            return log_loss(ym, pool(probs, softmax(z), self.method))

        res = minimize(objective, np.zeros(len(names)), method="Nelder-Mead",
                       options={"xatol": 1e-4, "fatol": 1e-7, "maxiter": 4000})
        w = softmax(res.x)
        w = (1 - self.shrinkage) * w + self.shrinkage / len(names)
        self.weights_ = dict(zip(names, w))
        return self

    def set_equal(self, names) -> "Ensemble":
        names = list(names)
        self.weights_ = {n: 1 / len(names) for n in names}
        return self

    def predict_proba(self, components: dict[str, np.ndarray]) -> np.ndarray:
        """Pool available components; rows where a component is NaN (e.g. no
        odds) fall back to the remaining components with renormalised weights."""
        names = [n for n in self.weights_ if n in components]
        n = len(next(iter(components.values())))
        out = np.full((n, 3), np.nan)
        avail = np.stack([np.isfinite(components[k]).all(axis=1) for k in names], axis=1)
        for pattern in {tuple(r) for r in avail}:
            rows = (avail == pattern).all(axis=1)
            use = [k for k, ok in zip(names, pattern) if ok]
            if not use:
                continue
            w = np.array([self.weights_[k] for k in use])
            out[rows] = pool([components[k][rows] for k in use], w / w.sum(), self.method)
        return out
