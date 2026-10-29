"""Walk through the main features of the package from Python.

Run from the project folder:  python examples/quickstart.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)

from football_predictor import (  # noqa: E402
    FootballPredictor,
    PredictorConfig,
    load_matches,
    simulate_season,
    walk_forward,
)
from football_predictor.reporting import format_match_report  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data" / "synthetic_league.csv"

# 1. Load results. Any football-data.co.uk CSV works the same way.
matches = load_matches(DATA)
print(matches.tail())

# 2. Honest evaluation: refit every two weeks, forecast the next two weeks.
config = PredictorConfig(ml_kind="logistic", refit_every_days=14)
bt = walk_forward(matches, config)
print(bt.metrics().round(4))
print(bt.betting(min_edge=0.05, staking="flat").summary)

# 3. Fit on everything and forecast a match with all derived markets.
model = FootballPredictor(config).fit(matches)
print(format_match_report(model.predict_match("Team A", "Team G", odds=(2.05, 3.5, 3.7))))

# 4. Forecast a list of fixtures in one go.
fixtures = pd.DataFrame({
    "home_team": ["Team B", "Team C", "Team D"],
    "away_team": ["Team E", "Team F", "Team H"],
    "date": ["2024-08-17"] * 3,
})
print(model.predict(fixtures)[["home_team", "away_team", "ensemble_home", "ensemble_draw",
                               "ensemble_away", "xg_home", "xg_away", "prediction"]].round(3))

# 5. Project the rest of a season from its midpoint.
season = matches[matches["season"] == matches["season"].max()]
cut = season["date"].quantile(0.5)
mid_model = FootballPredictor(config).fit(matches[matches["date"] <= cut])
table, positions = simulate_season(
    mid_model,
    season[season["date"] <= cut],
    season[season["date"] > cut][["date", "home_team", "away_team"]],
    n_sims=5000,
)
print(table.round(3).head(10))
