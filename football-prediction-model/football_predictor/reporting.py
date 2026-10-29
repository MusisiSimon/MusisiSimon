"""Text and chart output for predictions, backtests and simulations."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def _pct(p: float) -> str:
    return f"{100 * p:5.1f}%"


def format_match_report(pred: dict) -> str:
    """Human-readable version of :meth:`FootballPredictor.predict_match`."""
    p, mk, rt = pred["probabilities"], pred["markets"], pred["ratings"]
    lines = [
        "=" * 64,
        f"  {pred['fixture']}   ({pred['date']})",
        "=" * 64,
        f"  Prediction: {pred['prediction']}",
        "",
        "  1X2            prob    fair odds",
    ]
    for o in ("home", "draw", "away"):
        lines.append(f"  {o:<10} {_pct(p[o])}    {pred['fair_odds'][o]:>6.2f}")
    xg = mk["expected_goals"]
    lines += [
        "",
        f"  Expected goals: {xg['home']:.2f} - {xg['away']:.2f}   most likely score {mk['most_likely_score']}",
        "",
        "  Model components    home    draw    away   weight",
    ]
    for name, c in pred["components"].items():
        w = pred["ensemble_weights"].get(name, 0.0)
        lines.append(f"  {name:<16} {_pct(c['home'])} {_pct(c['draw'])} {_pct(c['away'])}   {w:5.2f}")
    lines += ["", "  Totals          over    under"]
    for line, v in mk["totals"].items():
        lines.append(f"  {line:>5} goals  {_pct(v['over'])}  {_pct(v['under'])}")
    lines += [
        "",
        f"  Both teams to score: yes {_pct(mk['btts']['yes'])}  no {_pct(mk['btts']['no'])}",
        f"  Clean sheet: home {_pct(mk['clean_sheet']['home'])}  away {_pct(mk['clean_sheet']['away'])}",
        f"  Double chance: 1X {_pct(mk['double_chance']['1X'])}  12 {_pct(mk['double_chance']['12'])}"
        f"  X2 {_pct(mk['double_chance']['X2'])}",
        "",
        "  Asian handicap (home)   win  half-win  push  half-loss  loss   fair",
    ]
    for line, v in mk["asian_handicap_home"].items():
        lines.append(
            f"  {line:>6}            {_pct(v['win'])} {_pct(v['half_win'])} {_pct(v['push'])}"
            f"  {_pct(v['half_loss'])} {_pct(v['loss'])}  {v['fair_odds']:5.2f}"
        )
    lines += ["", "  Correct score (top 8)"]
    for score, prob in list(mk["correct_score"].items())[:8]:
        lines.append(f"    {score:<6} {_pct(prob)}")
    lines += [
        "",
        "  Ratings            Elo     DC attack  DC defence",
        f"  {rt['home']['team']:<14} {rt['home']['elo']:7.0f}   {rt['home']['dc_attack']:+.3f}     {rt['home']['dc_defence']:+.3f}",
        f"  {rt['away']['team']:<14} {rt['away']['elo']:7.0f}   {rt['away']['dc_attack']:+.3f}     {rt['away']['dc_defence']:+.3f}",
        f"  home advantage {rt['dc_home_advantage']:+.3f} (log goals), rho {rt['dc_rho']:+.3f}",
    ]
    if pred.get("value"):
        lines += ["", "  Value vs offered odds     odds   market   model    edge"]
        for o, v in pred["value"].items():
            flag = "  <-- value" if v["edge"] > 0.03 else ""
            lines.append(
                f"  {o:<22} {v['odds']:6.2f}   {_pct(v['market_prob'])}  {_pct(v['model_prob'])}  {v['edge']:+6.1%}{flag}"
            )
    if pred["unknown_teams"]:
        lines += ["", f"  Note: no history for {', '.join(pred['unknown_teams'])}; rated as a promoted side."]
    lines.append("=" * 64)
    return "\n".join(lines)


def save_backtest_plots(result, out_dir: str | Path, model: str = "ensemble", betting=None) -> list[Path]:
    """Calibration curve, rolling RPS by model and (optionally) bankroll curve."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    # Calibration
    cal = result.calibration(model)
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.plot([0, 1], [0, 1], color="#999", lw=1, ls="--", label="perfect")
    ax.errorbar(cal["forecast"], cal["observed"], yerr=1.96 * cal["std_err"], fmt="o-", color="#2a6fdb",
                capsize=3, label=model)
    ax.set_xlabel("forecast probability")
    ax.set_ylabel("observed frequency")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("Calibration (all outcomes pooled)")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    p = out_dir / "calibration.png"
    fig.tight_layout()
    fig.savefig(p, dpi=130)
    plt.close(fig)
    paths.append(p)

    # Rolling RPS per model
    df = result.predictions.sort_values("date")
    y = np.eye(3)[df["outcome"].to_numpy()]
    fig, ax = plt.subplots(figsize=(8, 4))
    for name in result.models:
        pr = df[[f"{name}_{o}" for o in ("home", "draw", "away")]].to_numpy()
        if not np.isfinite(pr).all():
            continue
        r = (((np.cumsum(pr, 1) - np.cumsum(y, 1))[:, :2]) ** 2).sum(1) / 2
        ax.plot(df["date"], pd.Series(r).rolling(150, min_periods=50).mean().to_numpy(), label=name, lw=1.4)
    ax.set_ylabel("RPS (rolling 150 matches, lower is better)")
    ax.set_title("Out-of-sample accuracy over time")
    ax.legend(frameon=False, ncol=3, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    p = out_dir / "rolling_rps.png"
    fig.tight_layout()
    fig.savefig(p, dpi=130)
    plt.close(fig)
    paths.append(p)

    if betting is not None and not betting.bets.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(betting.bets["date"], betting.bets["bankroll"], color="#1b9e77")
        ax.axhline(betting.bets["bankroll"].iloc[0] - betting.bets["pnl"].iloc[0], color="#999", lw=1, ls="--")
        ax.set_title(f"Bankroll ({betting.summary['staking']} staking, {betting.summary['n_bets']} bets)")
        ax.spines[["top", "right"]].set_visible(False)
        p = out_dir / "bankroll.png"
        fig.tight_layout()
        fig.savefig(p, dpi=130)
        plt.close(fig)
        paths.append(p)
    return paths
