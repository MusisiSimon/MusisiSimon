"""League tables and Monte Carlo season simulation.

Remaining fixtures are played out many times by sampling scorelines from the
Dixon-Coles score matrix (optionally rescaled to the ensemble's 1X2), which
gives each team a distribution over final points and positions: title,
top-four and relegation chances, expected points, and so on.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .markets import rescale_to_1x2


def league_table(matches: pd.DataFrame, teams: list[str] | None = None) -> pd.DataFrame:
    """Standard table (3 points for a win) from played matches."""
    df = matches.dropna(subset=["home_goals", "away_goals"])
    teams = sorted(teams or set(df["home_team"]) | set(df["away_team"]))
    t = pd.DataFrame(0, index=teams, columns=["P", "W", "D", "L", "GF", "GA"], dtype=int)
    for r in df.itertuples(index=False):
        hg, ag = int(r.home_goals), int(r.away_goals)
        for team, gf, ga in ((r.home_team, hg, ag), (r.away_team, ag, hg)):
            t.loc[team, "P"] += 1
            t.loc[team, "GF"] += gf
            t.loc[team, "GA"] += ga
            t.loc[team, "W" if gf > ga else "D" if gf == ga else "L"] += 1
    t["GD"] = t["GF"] - t["GA"]
    t["Pts"] = 3 * t["W"] + t["D"]
    t = t.sort_values(["Pts", "GD", "GF"], ascending=False)
    t.index.name = "team"
    t = t.reset_index()
    t.index = np.arange(1, len(t) + 1)
    return t


def simulate_season(
    predictor,
    played_matches: pd.DataFrame,
    fixtures: pd.DataFrame,
    n_sims: int = 10000,
    seed: int = 0,
    use_ensemble: bool = True,
    zones: dict[str, tuple[int, int]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Simulate ``fixtures`` (remaining games) on top of ``played_matches``.

    ``predictor`` is a fitted :class:`FootballPredictor`. ``zones`` maps a
    label to an inclusive (from, to) finishing-position range; the default is
    title, top 4 and the bottom three.

    Returns ``(summary, position_probabilities)``.
    """
    rng = np.random.default_rng(seed)
    table = league_table(played_matches)
    teams = sorted(set(table["team"]) | set(fixtures["home_team"]) | set(fixtures["away_team"]))
    n = len(teams)
    zones = zones or {"title": (1, 1), "top4": (1, 4), "relegation": (n - 2, n)}
    ti = {t: i for i, t in enumerate(teams)}

    base = table.set_index("team").reindex(teams).fillna(0)
    pts = np.tile(base["Pts"].to_numpy(float), (n_sims, 1))
    gd = np.tile(base["GD"].to_numpy(float), (n_sims, 1))
    gf = np.tile(base["GF"].to_numpy(float), (n_sims, 1))

    ens = predictor.predict(fixtures) if use_ensemble and len(fixtures) else None
    for k, r in enumerate(fixtures.itertuples(index=False)):
        m = predictor.dc.score_matrix(r.home_team, r.away_team)
        if ens is not None:
            target = ens.iloc[k][["ensemble_home", "ensemble_draw", "ensemble_away"]].to_numpy(float)
            m = rescale_to_1x2(m, target)
        size = m.shape[0]
        draws = rng.choice(m.size, size=n_sims, p=m.ravel())
        hg, ag = np.divmod(draws, size)
        h, a = ti[r.home_team], ti[r.away_team]
        pts[:, h] += np.where(hg > ag, 3, np.where(hg == ag, 1, 0))
        pts[:, a] += np.where(ag > hg, 3, np.where(hg == ag, 1, 0))
        gd[:, h] += hg - ag
        gd[:, a] += ag - hg
        gf[:, h] += hg
        gf[:, a] += ag

    # Rank by points, then goal difference, then goals scored, then coin flip.
    key = pts * 1e6 + gd * 1e3 + gf + rng.random(pts.shape) * 0.5
    order = np.argsort(-key, axis=1)
    pos = np.empty_like(order)
    pos[np.arange(n_sims)[:, None], order] = np.arange(1, n + 1)

    pos_probs = pd.DataFrame(
        [(pos == p).mean(axis=0) for p in range(1, n + 1)], index=range(1, n + 1), columns=teams
    ).T
    summary = pd.DataFrame({
        "team": teams,
        "current_pts": base["Pts"].to_numpy(int),
        "played": base["P"].to_numpy(int),
        "exp_pts": pts.mean(axis=0),
        "pts_p10": np.percentile(pts, 10, axis=0),
        "pts_p90": np.percentile(pts, 90, axis=0),
        "exp_gd": gd.mean(axis=0),
        "exp_position": pos.mean(axis=0),
    })
    for label, (lo, hi) in zones.items():
        summary[f"p_{label}"] = ((pos >= lo) & (pos <= hi)).mean(axis=0)
    summary = summary.sort_values("exp_pts", ascending=False).reset_index(drop=True)
    summary.index += 1
    pos_probs = pos_probs.loc[summary["team"]]
    return summary, pos_probs
