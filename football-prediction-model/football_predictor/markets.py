"""Score-matrix maths shared by every goal-based model.

A goal model yields a matrix ``M`` where ``M[i, j]`` is the probability that
the home side scores ``i`` and the away side scores ``j``. Every betting market
(1X2, totals, both-teams-to-score, handicaps, correct score, ...) is a sum over
cells of that matrix, so this module turns one matrix into a full price sheet.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import poisson

DEFAULT_MAX_GOALS = 10


def dixon_coles_tau(lam: float, mu: float, rho: float) -> np.ndarray:
    """2x2 low-score correction factors of Dixon & Coles (1997)."""
    return np.array(
        [
            [1.0 - lam * mu * rho, 1.0 + lam * rho],
            [1.0 + mu * rho, 1.0 - rho],
        ]
    )


def score_matrix(lam: float, mu: float, rho: float = 0.0, max_goals: int = DEFAULT_MAX_GOALS) -> np.ndarray:
    """Joint home/away goal distribution, Poisson with Dixon-Coles correction.

    ``rho < 0`` raises the probability of 0-0 and 1-1 and lowers 1-0 and 0-1,
    matching the excess of low-scoring draws seen in real football.
    """
    g = np.arange(max_goals + 1)
    m = np.outer(poisson.pmf(g, lam), poisson.pmf(g, mu))
    m[:2, :2] *= dixon_coles_tau(lam, mu, rho)
    m = np.clip(m, 0.0, None)
    return m / m.sum()


def outcome_probs(m: np.ndarray) -> np.ndarray:
    """[P(home win), P(draw), P(away win)] from a score matrix."""
    return np.array([np.tril(m, -1).sum(), np.trace(m), np.triu(m, 1).sum()])


def goal_difference_distribution(m: np.ndarray) -> dict[int, float]:
    """P(home goals - away goals = d) for every reachable d."""
    n = m.shape[0]
    return {d: float(np.trace(m, offset=-d)) for d in range(-(n - 1), n)}


def asian_handicap(m: np.ndarray, line: float) -> dict[str, float]:
    """Home-side Asian handicap settlement probabilities for ``line``.

    ``line`` is applied to the home team (``-0.5`` means home must win). Quarter
    lines are split into the two adjacent half/whole lines, as bookmakers do.
    Returns probabilities of a full win, half win, push, half loss and full loss
    for a home bet, plus the fair decimal price ignoring pushes.
    """
    if abs(line * 4 - round(line * 4)) > 1e-9:
        raise ValueError("Asian handicap lines must be multiples of 0.25")
    gd = goal_difference_distribution(m)

    def settle(ln: float) -> dict[str, float]:
        win = sum(p for d, p in gd.items() if d + ln > 0)
        push = sum(p for d, p in gd.items() if abs(d + ln) < 1e-9)
        return {"win": win, "push": push, "loss": 1 - win - push}

    if abs(line * 2 - round(line * 2)) < 1e-9:  # whole or half line
        s = settle(line)
        res = {"win": s["win"], "half_win": 0.0, "push": s["push"], "half_loss": 0.0, "loss": s["loss"]}
    else:  # quarter line = half stake on each neighbour
        lo, hi = line - 0.25, line + 0.25
        a, b = settle(lo), settle(hi)
        # With a quarter line one leg is always a half line (no push), so each
        # goal difference produces one of: both win, win+push, both lose, loss+push.
        both_win = min(a["win"], b["win"])
        both_lose = min(a["loss"], b["loss"])
        res = {
            "win": both_win,
            "half_win": max(a["win"], b["win"]) - both_win,
            "push": 0.0,
            "half_loss": max(a["loss"], b["loss"]) - both_lose,
            "loss": both_lose,
        }
    # Fair price: expected return of 1 unit stake = 1.
    #   win -> o, half_win -> (o+1)/2, push -> 1, half_loss -> 0.5, loss -> 0
    # Solve for o.
    w, hw, p, hl = res["win"], res["half_win"], res["push"], res["half_loss"]
    denom = w + hw / 2
    res["fair_odds"] = float((1 - hw / 2 - p - hl / 2) / denom) if denom > 0 else float("inf")
    return res


def market_sheet(
    m: np.ndarray,
    total_lines=(0.5, 1.5, 2.5, 3.5, 4.5),
    handicap_lines=(-1.5, -1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 1.5),
    top_scores: int = 10,
) -> dict:
    """Derive every common market from a score matrix."""
    n = m.shape[0]
    g = np.arange(n)
    home_marg, away_marg = m.sum(axis=1), m.sum(axis=0)
    tot = np.add.outer(g, g)
    p1x2 = outcome_probs(m)

    totals = {}
    for line in total_lines:
        over = float(m[tot > line].sum())
        totals[f"{line}"] = {"over": over, "under": 1 - over}

    scores = sorted(
        ((f"{i}-{j}", float(m[i, j])) for i in range(n) for j in range(n)),
        key=lambda kv: kv[1],
        reverse=True,
    )[:top_scores]

    return {
        "expected_goals": {"home": float(g @ home_marg), "away": float(g @ away_marg)},
        "1x2": {"home": float(p1x2[0]), "draw": float(p1x2[1]), "away": float(p1x2[2])},
        "double_chance": {
            "1X": float(p1x2[0] + p1x2[1]),
            "12": float(p1x2[0] + p1x2[2]),
            "X2": float(p1x2[1] + p1x2[2]),
        },
        "draw_no_bet": {
            "home": float(p1x2[0] / (p1x2[0] + p1x2[2])),
            "away": float(p1x2[2] / (p1x2[0] + p1x2[2])),
        },
        "totals": totals,
        "btts": {"yes": float(m[1:, 1:].sum()), "no": float(1 - m[1:, 1:].sum())},
        "clean_sheet": {"home": float(away_marg[0]), "away": float(home_marg[0])},
        "team_goals": {
            "home": {str(k): float(home_marg[k]) for k in range(min(n, 6))},
            "away": {str(k): float(away_marg[k]) for k in range(min(n, 6))},
        },
        "asian_handicap_home": {f"{ln:+}": asian_handicap(m, ln) for ln in handicap_lines},
        "correct_score": dict(scores),
        "most_likely_score": scores[0][0],
    }


def fair_odds(p: float) -> float:
    """Decimal odds with no margin for probability ``p``."""
    return float("inf") if p <= 0 else 1.0 / p


def rescale_to_1x2(m: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Rescale a score matrix so its 1X2 probabilities equal ``target``.

    The home-win, draw and away-win regions are each multiplied by a constant.
    This keeps the goal model's shape *within* each region (which scorelines
    make up a home win, etc.) while adopting the 1X2 split from a better
    calibrated source such as the ensemble, so every derived market stays
    consistent with the headline probabilities.
    """
    current = outcome_probs(m)
    n = m.shape[0]
    i, j = np.indices((n, n))
    region = np.where(i > j, 0, np.where(i == j, 1, 2))
    scale = np.asarray(target, float) / np.maximum(current, 1e-15)
    out = m * scale[region]
    return out / out.sum()
