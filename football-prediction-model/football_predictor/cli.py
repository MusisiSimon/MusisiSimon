"""Command-line interface.

    python -m football_predictor demo
    python -m football_predictor generate --out data/synthetic.csv
    python -m football_predictor download --league E0 --seasons 2122 2223 2324 --out data/E0
    python -m football_predictor backtest --data data/E0 --plots reports/
    python -m football_predictor predict --data data/E0 --home Arsenal --away Chelsea --odds 1.9 3.6 4.2
    python -m football_predictor predict --data data/E0 --fixtures fixtures.csv --out predictions.csv
    python -m football_predictor ratings --data data/E0
    python -m football_predictor simulate --data data/E0 --fixtures remaining.csv --sims 20000
    python -m football_predictor tune --data data/E0
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pandas as pd

from .backtest import walk_forward
from .data import download_football_data, generate_synthetic_league, load_matches, played
from .dixon_coles import tune_time_decay
from .predictor import FootballPredictor, PredictorConfig
from .reporting import format_match_report, save_backtest_plots
from .simulation import league_table, simulate_season

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 30)


def _config(args) -> PredictorConfig:
    cfg = PredictorConfig()
    if getattr(args, "ml", None):
        cfg.ml_kind = args.ml
    if getattr(args, "xi", None) is not None:
        cfg.dc_xi = args.xi
    if getattr(args, "with_market", False):
        cfg.include_market_component = True
    if getattr(args, "market_features", False):
        cfg.use_market_features = True
    return cfg


def _section(title: str) -> None:
    print(f"\n{'-' * 72}\n{title}\n{'-' * 72}")


def _print_backtest(bt, args) -> None:
    _section("Out-of-sample metrics (lower log loss / Brier / RPS is better)")
    print(bt.metrics().round(4).to_string())
    _section("Ensemble by season")
    print(bt.metrics_by_season().round(4).to_string())
    _section("Ensemble weights at the last refit")
    print(bt.weights_history.iloc[-1].drop(["block_start", "n_oos"]).astype(float).round(3).to_string())
    _section("Calibration of the ensemble")
    print(bt.calibration().round(3).to_string(index=False))
    if bt.predictions[["odds_home", "odds_draw", "odds_away"]].notna().all(axis=1).any():
        _section(f"Betting simulation (edge > {args.min_edge:.0%})")
        for staking in ("flat", "kelly"):
            b = bt.betting(min_edge=args.min_edge, staking=staking)
            s = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in b.summary.items()}
            print(json.dumps(s))
        print("Note: past betting returns, and any return on synthetic odds, do not predict future profit.")


def cmd_generate(args) -> None:
    df, _ = generate_synthetic_league(n_teams=args.teams, n_seasons=args.seasons, seed=args.seed)
    df.to_csv(args.out, index=False)
    print(f"wrote {len(df)} matches to {args.out}")


def cmd_download(args) -> None:
    paths = download_football_data(args.league, args.seasons, args.out)
    for p in paths:
        print(f"saved {p}")


def cmd_backtest(args) -> None:
    df = load_matches(args.data)
    print(f"{len(played(df))} played matches, {df['season'].nunique()} seasons, "
          f"{len(set(df['home_team']))} teams")
    bt = walk_forward(df, _config(args), test_start=args.test_start, refit_every_days=args.refit_days,
                      verbose=args.verbose)
    _print_backtest(bt, args)
    if args.out:
        bt.predictions.to_csv(args.out, index=False)
        print(f"\nper-match predictions written to {args.out}")
    if args.plots:
        betting = bt.betting(min_edge=args.min_edge) if bt.predictions["odds_home"].notna().any() else None
        for p in save_backtest_plots(bt, args.plots, betting=betting):
            print(f"saved {p}")


def cmd_predict(args) -> None:
    df = load_matches(args.data)
    model = FootballPredictor(_config(args)).fit(df)
    if args.fixtures:
        fx = pd.read_csv(args.fixtures)
        fx = fx.rename(columns={"HomeTeam": "home_team", "AwayTeam": "away_team", "Date": "date"})
        out = model.predict(fx)
        print(out.round({c: 3 for c in out.select_dtypes("number").columns}).to_string(index=False))
        if args.out:
            out.to_csv(args.out, index=False)
            print(f"\nwritten to {args.out}")
        return
    if not (args.home and args.away):
        sys.exit("give --home and --away, or --fixtures FILE")
    pred = model.predict_match(args.home, args.away, date=args.date, odds=args.odds, neutral=args.neutral)
    if args.json:
        print(json.dumps(pred, indent=2, default=float))
    else:
        print(format_match_report(pred))


def cmd_ratings(args) -> None:
    df = load_matches(args.data)
    model = FootballPredictor(_config(args)).fit(df, learn_weights=False)
    table = model.dc.ratings_table()
    elo = model.builder_.elo.ratings
    table["elo"] = table["team"].map(elo)
    print(table.round(3).to_string())


def cmd_simulate(args) -> None:
    df = load_matches(args.data)
    if args.fixtures:
        fixtures = pd.read_csv(args.fixtures).rename(
            columns={"HomeTeam": "home_team", "AwayTeam": "away_team", "Date": "date"})
        season = df["season"].max()
        played_now = played(df[df["season"] == season])
        history = df
    else:
        # No fixture list: replay the second half of the latest season to show
        # how well a mid-season projection matches what actually happened.
        season = df["season"].max()
        cur = df[df["season"] == season]
        cut = cur["date"].quantile(args.cut)
        history = df[df["date"] <= cut]
        played_now = played(cur[cur["date"] <= cut])
        fixtures = cur[cur["date"] > cut][["date", "home_team", "away_team"]]
        print(f"No --fixtures given: simulating {season} from {cut.date()} ({len(fixtures)} games left)")
    model = FootballPredictor(_config(args)).fit(history)
    summary, pos = simulate_season(model, played_now, fixtures, n_sims=args.sims, seed=args.seed)
    _section(f"Projected final table ({args.sims} simulations)")
    print(summary.round(3).to_string())
    if not args.fixtures:
        _section("Actual final table")
        print(league_table(cur)[["team", "P", "W", "D", "L", "GD", "Pts"]].to_string())
    if args.out:
        summary.to_csv(args.out)
        pos.to_csv(args.out.replace(".csv", "_positions.csv"))


def cmd_tune(args) -> None:
    df = load_matches(args.data)
    print("Dixon-Coles time decay (xi per day) by walk-forward log loss:")
    print(tune_time_decay(df).round(5).to_string(index=False))


def cmd_demo(args) -> None:
    _section("1. Generating a synthetic 20-team league, 5 seasons (known true strengths)")
    df, truth = generate_synthetic_league(seed=args.seed)
    print(f"{len(df)} matches  |  true home advantage {truth.home_advantage}, rho {truth.rho}")
    print(df.head(5).to_string(index=False))

    _section("2. Walk-forward backtest over the last two seasons")
    bt = walk_forward(df, _config(args))
    _print_backtest(bt, args)

    _section("3. Fit on all data and recover the true parameters")
    model = FootballPredictor(_config(args)).fit(df)
    dc = model.dc
    print(f"home advantage: true {truth.home_advantage:.3f}  estimated {dc.home_adv_:.3f}")
    print(f"rho:            true {truth.rho:.3f}  estimated {dc.rho_:.3f}")
    s = df["season"].max()
    att_corr = np.corrcoef([dc.attack_[t] for t in dc.teams_], [truth.attack[s][t] for t in dc.teams_])[0, 1]
    def_corr = np.corrcoef([dc.defence_[t] for t in dc.teams_], [truth.defence[s][t] for t in dc.teams_])[0, 1]
    print(f"correlation with true attack {att_corr:.3f}, defence {def_corr:.3f}")
    print("\nTop of the Dixon-Coles ratings table:")
    print(dc.ratings_table().head(8).round(3).to_string())

    _section("4. Full prediction for a single match")
    top = dc.ratings_table()["team"].tolist()
    print(format_match_report(model.predict_match(top[0], top[1], odds=(2.0, 3.5, 3.9))))

    _section("5. Mid-season Monte Carlo projection of the last season")
    cur = df[df["season"] == s]
    cut = cur["date"].quantile(0.5)
    model_half = FootballPredictor(_config(args)).fit(df[df["date"] <= cut])
    summary, _ = simulate_season(model_half, cur[cur["date"] <= cut],
                                 cur[cur["date"] > cut][["date", "home_team", "away_team"]], n_sims=5000)
    actual = league_table(cur).reset_index().rename(columns={"index": "actual_pos"})
    summary = summary.merge(actual[["team", "actual_pos", "Pts"]], on="team")
    summary.index += 1
    cols = ["team", "current_pts", "exp_pts", "pts_p10", "pts_p90", "p_title", "p_top4", "p_relegation",
            "actual_pos", "Pts"]
    print(summary[cols].round(3).to_string())


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="football_predictor", description="Football match prediction toolkit")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, data=True):
        if data:
            p.add_argument("--data", required=True, nargs="+", help="CSV file(s) or folder(s) of results")
        p.add_argument("--ml", choices=["logistic", "gbm"], help="ML component (default logistic)")
        p.add_argument("--xi", type=float, help="Dixon-Coles time decay per day (default 0.0019)")
        p.add_argument("--with-market", action="store_true", help="add bookmaker odds as an ensemble member")
        p.add_argument("--market-features", action="store_true", help="feed bookmaker odds to the ML model")
        p.add_argument("--seed", type=int, default=7)

    p = sub.add_parser("demo", help="end-to-end demo on synthetic data")
    common(p, data=False)
    p.add_argument("--min-edge", type=float, default=0.05)
    p.set_defaults(func=cmd_demo)

    p = sub.add_parser("generate", help="write a synthetic league CSV")
    p.add_argument("--out", default="data/synthetic.csv")
    p.add_argument("--teams", type=int, default=20)
    p.add_argument("--seasons", type=int, default=5)
    p.add_argument("--seed", type=int, default=7)
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("download", help="download football-data.co.uk CSVs")
    p.add_argument("--league", default="E0")
    p.add_argument("--seasons", nargs="+", required=True, help="e.g. 2122 2223 2324")
    p.add_argument("--out", default="data")
    p.set_defaults(func=cmd_download)

    p = sub.add_parser("backtest", help="walk-forward evaluation")
    common(p)
    p.add_argument("--test-start", help="first date to forecast (default: second-to-last season)")
    p.add_argument("--refit-days", type=int, help="refit interval in days (default 14)")
    p.add_argument("--min-edge", type=float, default=0.05)
    p.add_argument("--out", help="write per-match predictions CSV")
    p.add_argument("--plots", help="folder for calibration / RPS / bankroll charts")
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(func=cmd_backtest)

    p = sub.add_parser("predict", help="predict one match or a fixture list")
    common(p)
    p.add_argument("--home")
    p.add_argument("--away")
    p.add_argument("--date")
    p.add_argument("--odds", type=float, nargs=3, metavar=("HOME", "DRAW", "AWAY"))
    p.add_argument("--neutral", action="store_true")
    p.add_argument("--fixtures", help="CSV with home_team, away_team[, date, odds_*]")
    p.add_argument("--out")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_predict)

    p = sub.add_parser("ratings", help="current team ratings")
    common(p)
    p.set_defaults(func=cmd_ratings)

    p = sub.add_parser("simulate", help="Monte Carlo season projection")
    common(p)
    p.add_argument("--fixtures", help="CSV of remaining fixtures (home_team, away_team, date)")
    p.add_argument("--sims", type=int, default=10000)
    p.add_argument("--cut", type=float, default=0.5, help="without --fixtures: fraction of season played")
    p.add_argument("--out")
    p.set_defaults(func=cmd_simulate)

    p = sub.add_parser("tune", help="choose the Dixon-Coles time decay")
    common(p)
    p.set_defaults(func=cmd_tune)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
