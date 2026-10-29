import numpy as np
import pandas as pd
import pytest
from scipy.optimize import check_grad

from football_predictor import (
    DixonColesModel,
    EloRatings,
    FootballPredictor,
    OrderedLogit,
    PredictorConfig,
    build_features,
    generate_synthetic_league,
    implied_probabilities,
    league_table,
    simulate_season,
    standardize,
    walk_forward,
)
from football_predictor.dixon_coles import _neg_log_lik
from football_predictor.evaluation import brier, log_loss, rps
from football_predictor.markets import asian_handicap, market_sheet, outcome_probs, rescale_to_1x2, score_matrix


@pytest.fixture(scope="module")
def league():
    return generate_synthetic_league(n_teams=12, n_seasons=4, seed=3)


# ------------------------------------------------------------------ data
def test_standardize_football_data_columns():
    raw = pd.DataFrame({
        "Date": ["17/08/2024", "18/08/2024"],
        "HomeTeam": ["Arsenal ", "Chelsea"],
        "AwayTeam": ["Wolves", "Man City"],
        "FTHG": [2, 0], "FTAG": [0, 2],
        "B365H": [1.3, 4.0], "B365D": [5.5, 3.8], "B365A": [10.0, 1.8],
    })
    df = standardize(raw)
    assert list(df["home_team"]) == ["Arsenal", "Chelsea"]
    assert df["date"].iloc[0] == pd.Timestamp("2024-08-17")
    assert df["season"].iloc[0] == "2024-25"
    assert df["odds_home"].iloc[1] == 4.0


def test_implied_probabilities_remove_margin():
    odds = np.array([[1.9, 3.6, 4.2], [1.2, 7.0, 15.0]])
    for method in ("basic", "power"):
        p = implied_probabilities(odds, method)
        np.testing.assert_allclose(p.sum(axis=1), 1)
    # Power method shortens the favourite less than proportional scaling does.
    assert implied_probabilities(odds, "power")[1, 0] > implied_probabilities(odds, "basic")[1, 0]


# --------------------------------------------------------------- markets
def test_score_matrix_and_markets_consistent():
    m = score_matrix(1.6, 1.1, -0.1)
    assert m.sum() == pytest.approx(1)
    p = outcome_probs(m)
    sheet = market_sheet(m)
    assert sheet["1x2"]["home"] == pytest.approx(p[0])
    assert sheet["totals"]["2.5"]["over"] + sheet["totals"]["2.5"]["under"] == pytest.approx(1)
    assert sheet["expected_goals"]["home"] == pytest.approx(1.6, abs=0.02)
    # AH -0.5 is the same bet as a home win; AH 0 voids on a draw.
    assert sheet["asian_handicap_home"]["-0.5"]["win"] == pytest.approx(p[0])
    assert sheet["asian_handicap_home"]["+0.0"]["fair_odds"] == pytest.approx((1 - p[1]) / p[0])


def test_asian_quarter_line_splits_stake():
    m = score_matrix(1.4, 1.2, 0.0)
    p = outcome_probs(m)
    ah = asian_handicap(m, -0.25)  # half on -0.5, half on 0
    assert ah["win"] == pytest.approx(p[0])
    assert ah["half_loss"] == pytest.approx(p[1])
    assert ah["loss"] == pytest.approx(p[2])


def test_rescale_to_1x2_hits_target():
    m = score_matrix(1.3, 1.0, -0.05)
    target = np.array([0.5, 0.25, 0.25])
    np.testing.assert_allclose(outcome_probs(rescale_to_1x2(m, target)), target)


# ------------------------------------------------------------ evaluation
def test_scoring_rules_known_values():
    y = np.array([0])
    perfect = np.array([[1.0, 0.0, 0.0]])
    assert rps(y, perfect) == 0 and brier(y, perfect) == 0
    # Predicting a draw when the home side wins is better than predicting an away win under RPS.
    assert rps(y, np.array([[0, 1.0, 0]])) < rps(y, np.array([[0, 0, 1.0]]))
    assert rps(y, np.array([[0, 1.0, 0]])) == pytest.approx(0.5)
    assert log_loss(y, np.array([[0.5, 0.25, 0.25]])) == pytest.approx(np.log(2))


# ----------------------------------------------------------- Dixon-Coles
def test_dixon_coles_gradient(league):
    df, _ = league
    teams = sorted(set(df.home_team))
    idx = {t: i for i, t in enumerate(teams)}
    hi, ai = df.home_team.map(idx).to_numpy(), df.away_team.map(idx).to_numpy()
    x, y = df.home_goals.to_numpy(float), df.away_goals.to_numpy(float)
    w = np.random.default_rng(0).random(len(x))
    n = len(teams)
    p0 = np.random.default_rng(1).normal(0, 0.2, 2 * n + 3)
    p0[-1] = -0.05
    err = check_grad(lambda p: _neg_log_lik(p, hi, ai, x, y, w, n, 0.5)[0],
                     lambda p: _neg_log_lik(p, hi, ai, x, y, w, n, 0.5)[1], p0)
    assert err < 1e-3


def test_dixon_coles_recovers_truth():
    df, truth = generate_synthetic_league(n_teams=20, n_seasons=5, seed=11)
    dc = DixonColesModel().fit(df)
    s = df["season"].max()
    att = np.corrcoef([dc.attack_[t] for t in dc.teams_], [truth.attack[s][t] for t in dc.teams_])[0, 1]
    assert att > 0.85
    assert dc.home_adv_ == pytest.approx(truth.home_advantage, abs=0.08)
    assert dc.rho_ < 0
    p = dc.predict_proba(dc.teams_[0], dc.teams_[1])
    assert p.sum() == pytest.approx(1)


def test_unknown_team_gets_weak_prior(league):
    df, _ = league
    dc = DixonColesModel().fit(df)
    best = dc.ratings_table()["team"].iloc[0]
    p = dc.predict_proba(best, "Promoted FC")
    assert p[0] > p[2]


# ------------------------------------------------------------------- Elo
def test_elo_zero_sum_and_margin():
    elo = EloRatings()
    elo.update("A", "B", 3, 0)
    assert elo.ratings["A"] + elo.ratings["B"] == pytest.approx(3000)
    big = elo.ratings["A"] - 1500
    elo2 = EloRatings()
    elo2.update("A", "B", 1, 0)
    assert big > elo2.ratings["A"] - 1500


def test_ordered_logit_monotone():
    rng = np.random.default_rng(0)
    x = rng.normal(0, 150, 3000)
    p_home = 1 / (1 + np.exp(-(x / 150 - 0.2)))
    y = np.where(rng.random(3000) < p_home, 0, rng.choice([1, 2], 3000, p=[0.45, 0.55]))
    model = OrderedLogit().fit(x, y)
    p = model.predict_proba(np.array([-300.0, 0.0, 300.0]))
    np.testing.assert_allclose(p.sum(axis=1), 1)
    assert p[0, 0] < p[1, 0] < p[2, 0]
    assert p[0, 2] > p[2, 2]


# -------------------------------------------------------------- features
def test_features_have_no_lookahead(league):
    df, _ = league
    f1, _ = build_features(df)
    # Change every result after the cut; features up to and including the
    # cut date must not move.
    cut = df["date"].iloc[len(df) // 2]
    tampered = df.copy()
    later = tampered["date"] > cut
    tampered.loc[later, ["home_goals", "away_goals"]] = tampered.loc[later, ["away_goals", "home_goals"]].to_numpy() + 3
    f2, _ = build_features(tampered)
    early = ~later
    pd.testing.assert_frame_equal(f1[early], f2[early])
    assert not f1[later].equals(f2[later])


def test_same_day_matches_do_not_see_each_other(league):
    df, _ = league
    first_day = df[df["date"] == df["date"].min()]
    f, _ = build_features(df)
    assert (f.loc[first_day.index, "h_experience"] == 0).all()


# ------------------------------------------------------- full pipeline
def test_walk_forward_beats_base_rate(league):
    df, _ = league
    bt = walk_forward(df, PredictorConfig(refit_every_days=28))
    m = bt.metrics()
    assert m.loc["ensemble", "rps"] < m.loc["base_rate", "rps"]
    assert m.loc["dixon_coles", "log_loss"] < m.loc["base_rate", "log_loss"]
    p = bt.probs("ensemble")
    np.testing.assert_allclose(p.sum(axis=1), 1)
    # Every forecast was made before its match.
    assert (bt.predictions["date"] >= pd.Timestamp(bt.weights_history["block_start"].min())).all()


def test_predictor_end_to_end(league):
    df, _ = league
    model = FootballPredictor().fit(df)
    assert sum(model.ensemble.weights_.values()) == pytest.approx(1)
    teams = model.dc.teams_
    pred = model.predict_match(teams[0], teams[1], odds=(2.0, 3.4, 3.8))
    probs = pred["probabilities"]
    assert sum(probs.values()) == pytest.approx(1)
    assert pred["markets"]["1x2"]["home"] == pytest.approx(probs["home"], abs=1e-9)
    assert set(pred["value"]) == {"home", "draw", "away"}

    # Predicting must not change the fitted state.
    before = dict(model.builder_.elo.ratings)
    model.predict(pd.DataFrame({"home_team": [teams[2]], "away_team": [teams[3]], "date": ["2035-01-01"]}))
    assert model.builder_.elo.ratings == before


def test_season_simulation(league):
    df, _ = league
    cur = df[df["season"] == df["season"].max()]
    cut = cur["date"].quantile(0.5)
    model = FootballPredictor().fit(df[df["date"] <= cut], learn_weights=False)
    summary, pos = simulate_season(model, cur[cur["date"] <= cut],
                                   cur[cur["date"] > cut][["date", "home_team", "away_team"]], n_sims=2000)
    n = len(summary)
    assert summary["p_title"].sum() == pytest.approx(1)
    assert summary["p_relegation"].sum() == pytest.approx(3)
    np.testing.assert_allclose(pos.sum(axis=1), 1)
    np.testing.assert_allclose(pos.sum(axis=0), 1)
    # Points can only go up from the current table.
    assert (summary["pts_p10"] >= summary["current_pts"]).all()
    assert n == 12
    t = league_table(cur)
    assert t["Pts"].sum() == 3 * (t["W"].sum()) + t["D"].sum()


def test_elo_promoted_team_starts_below_average():
    elo = EloRatings()
    elo.start_season("2023-24")
    elo.update("A", "B", 1, 0)
    assert elo.rating("C") == pytest.approx(1500)  # opening season: everyone level
    elo.start_season("2024-25")
    assert elo.rating("Promoted") < 1500
