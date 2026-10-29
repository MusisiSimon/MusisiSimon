"""Football match prediction: Dixon-Coles, Elo, ML features and an ensemble."""

from .backtest import BacktestResult, simulate_betting, walk_forward
from .data import (
    download_football_data,
    generate_synthetic_league,
    implied_probabilities,
    load_matches,
    standardize,
)
from .dixon_coles import DixonColesModel, tune_time_decay
from .elo import EloRatings, OrderedLogit
from .ensemble import Ensemble
from .evaluation import brier, calibration_table, compare_models, log_loss, rps
from .features import FeatureBuilder, build_features
from .markets import market_sheet, score_matrix
from .ml_model import MLOutcomeModel
from .predictor import FootballPredictor, PredictorConfig
from .simulation import league_table, simulate_season

__all__ = [
    "BacktestResult",
    "DixonColesModel",
    "EloRatings",
    "Ensemble",
    "FeatureBuilder",
    "FootballPredictor",
    "MLOutcomeModel",
    "OrderedLogit",
    "PredictorConfig",
    "brier",
    "build_features",
    "calibration_table",
    "compare_models",
    "download_football_data",
    "generate_synthetic_league",
    "implied_probabilities",
    "league_table",
    "load_matches",
    "log_loss",
    "market_sheet",
    "rps",
    "score_matrix",
    "simulate_betting",
    "simulate_season",
    "standardize",
    "tune_time_decay",
    "walk_forward",
]

__version__ = "1.0.0"
