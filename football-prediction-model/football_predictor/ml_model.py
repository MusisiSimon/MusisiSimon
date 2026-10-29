"""Machine-learning outcome classifier on engineered features.

Two estimators are available:

* ``"logistic"`` - multinomial logistic regression with median imputation and
  standardisation. Robust with small samples and easy to interpret.
* ``"gbm"`` - histogram gradient boosting. Captures interactions (e.g. form
  only mattering when the Elo gap is small) and handles missing values
  natively, but needs more data.

Recent matches can be up-weighted with ``recency_halflife_days`` because the
relationship between features and outcomes drifts over time.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits


@dataclass
class MLOutcomeModel:
    kind: str = "logistic"
    recency_halflife_days: float | None = 540.0
    C: float = 0.05  # inverse regularisation strength for logistic regression
    random_state: int = 0

    features_: list[str] = field(default_factory=list, init=False)
    model_: object = field(default=None, init=False, repr=False)

    def _make(self):
        if self.kind == "logistic":
            return make_pipeline(
                SimpleImputer(strategy="median", keep_empty_features=True),
                StandardScaler(),
                LogisticRegression(C=self.C, max_iter=3000),
            )
        if self.kind == "gbm":
            return HistGradientBoostingClassifier(
                learning_rate=0.05,
                max_iter=250,
                max_leaf_nodes=12,
                min_samples_leaf=40,
                l2_regularization=2.0,
                early_stopping=True,
                validation_fraction=0.2,
                n_iter_no_change=25,
                random_state=self.random_state,
            )
        raise ValueError("kind must be 'logistic' or 'gbm'")

    def fit(self, X: pd.DataFrame, y, dates: pd.Series | None = None) -> "MLOutcomeModel":
        self.features_ = list(X.columns)
        weights = None
        if self.recency_halflife_days and dates is not None:
            age = (dates.max() - dates).dt.days.to_numpy(float)
            weights = 0.5 ** (age / self.recency_halflife_days)
        self.model_ = self._make()
        fit_kw = {}
        if weights is not None:
            key = "logisticregression__sample_weight" if self.kind == "logistic" else "sample_weight"
            fit_kw[key] = weights
        # A few thousand rows is far too small to benefit from parallel tree
        # building; extra OpenMP threads only add overhead.
        with threadpool_limits(limits=1, user_api="openmp"):
            self.model_.fit(X[self.features_], np.asarray(y), **fit_kw)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        with threadpool_limits(limits=1, user_api="openmp"):
            raw = self.model_.predict_proba(X[self.features_])
        # Re-order columns to [home, draw, away] even if a class was missing.
        out = np.full((len(X), 3), 1e-6)
        for j, c in enumerate(self.model_.classes_):
            out[:, int(c)] = raw[:, j]
        return out / out.sum(axis=1, keepdims=True)

    def feature_importance(self, X: pd.DataFrame | None = None, y=None, n_repeats: int = 5) -> pd.Series:
        """Logistic: mean |coefficient| on standardised features.
        GBM: permutation importance (needs ``X`` and ``y``), measured in log loss."""
        if self.kind == "logistic":
            coef = self.model_[-1].coef_
            return pd.Series(np.abs(coef).mean(axis=0), index=self.features_).sort_values(ascending=False)
        if X is None or y is None:
            raise ValueError("permutation importance needs X and y")
        r = permutation_importance(
            self.model_, X[self.features_], y, scoring="neg_log_loss",
            n_repeats=n_repeats, random_state=self.random_state,
        )
        return pd.Series(r.importances_mean, index=self.features_).sort_values(ascending=False)
