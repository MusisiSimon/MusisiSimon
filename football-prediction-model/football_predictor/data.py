"""Loading, cleaning and generating match data.

Every other module works on a single canonical DataFrame layout:

=====================  =====================================================
column                 meaning
=====================  =====================================================
date                   kick-off date (``datetime64``)
season                 season label, e.g. ``"2023-24"``
home_team / away_team  team names
home_goals/away_goals  full-time goals (NaN for unplayed fixtures)
home_shots/away_shots  total shots (optional)
home_sot / away_sot    shots on target (optional)
odds_home/draw/away    decimal 1X2 odds (optional)
=====================  =====================================================

The loader understands the CSV files published by football-data.co.uk (the most
common free source of historical results and odds) as well as files that
already use the canonical names.
"""

from __future__ import annotations

import io
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .markets import outcome_probs, score_matrix

CANONICAL_COLUMNS = [
    "date",
    "season",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "home_shots",
    "away_shots",
    "home_sot",
    "away_sot",
    "odds_home",
    "odds_draw",
    "odds_away",
]

# football-data.co.uk column names -> canonical names. For odds we try several
# bookmakers in order of preference and keep the first one that is present.
_FOOTBALL_DATA_MAP = {
    "Date": "date",
    "HomeTeam": "home_team",
    "AwayTeam": "away_team",
    "Home": "home_team",
    "Away": "away_team",
    "FTHG": "home_goals",
    "FTAG": "away_goals",
    "HG": "home_goals",
    "AG": "away_goals",
    "HS": "home_shots",
    "AS": "away_shots",
    "HST": "home_sot",
    "AST": "away_sot",
    "Season": "season",
}
_ODDS_PREFERENCE = [
    ("PSCH", "PSCD", "PSCA"),  # Pinnacle closing
    ("PSH", "PSD", "PSA"),  # Pinnacle
    ("AvgH", "AvgD", "AvgA"),  # market average
    ("B365H", "B365D", "B365A"),  # Bet365
    ("BbAvH", "BbAvD", "BbAvA"),  # older market average
]

FOOTBALL_DATA_URL = "https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def _infer_season(dates: pd.Series, start_month: int = 7) -> pd.Series:
    """Label each date with the European season it belongs to (Jul -> Jun)."""
    start_year = np.where(dates.dt.month >= start_month, dates.dt.year, dates.dt.year - 1)
    return pd.Series(
        [f"{y}-{str(y + 1)[-2:]}" for y in start_year], index=dates.index, dtype="object"
    )


def parse_dates(values: pd.Series, dayfirst: bool = True) -> pd.Series:
    """Parse ISO dates (2024-08-17) and football-data style dates (17/08/24, 17/08/2024)."""
    if pd.api.types.is_datetime64_any_dtype(values):
        return values
    s = values.astype("string").str.strip()
    iso = s.str.match(r"^\d{4}-\d{2}-\d{2}").fillna(False).to_numpy(bool)
    out = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    if iso.any():
        out[iso] = pd.to_datetime(s[iso].str[:10], format="%Y-%m-%d", errors="coerce")
    if (~iso).any():
        out[~iso] = pd.to_datetime(s[~iso], dayfirst=dayfirst, format="mixed", errors="coerce")
    return out


def standardize(df: pd.DataFrame, dayfirst: bool = True) -> pd.DataFrame:
    """Convert a raw results table into the canonical layout.

    Accepts football-data.co.uk style columns or canonical columns. Rows without
    team names or a parsable date are dropped; the result is sorted by date.
    """
    df = df.copy()
    df = df.rename(columns={k: v for k, v in _FOOTBALL_DATA_MAP.items() if k in df.columns})
    # Prefer canonical columns already present over a duplicate rename result.
    df = df.loc[:, ~df.columns.duplicated()]

    if not {"odds_home", "odds_draw", "odds_away"} <= set(df.columns):
        for h, d, a in _ODDS_PREFERENCE:
            if {h, d, a} <= set(df.columns):
                df["odds_home"], df["odds_draw"], df["odds_away"] = df[h], df[d], df[a]
                break

    missing = {"date", "home_team", "away_team"} - set(df.columns)
    if missing:
        raise ValueError(f"input is missing required columns: {sorted(missing)}")

    df["date"] = parse_dates(df["date"], dayfirst=dayfirst)
    df = df.dropna(subset=["date", "home_team", "away_team"])
    df["home_team"] = df["home_team"].astype(str).str.strip()
    df["away_team"] = df["away_team"].astype(str).str.strip()

    for col in CANONICAL_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    numeric = [c for c in CANONICAL_COLUMNS if c not in ("date", "season", "home_team", "away_team")]
    df[numeric] = df[numeric].apply(pd.to_numeric, errors="coerce")

    if df["season"].isna().all():
        df["season"] = _infer_season(df["date"])
    else:
        df["season"] = df["season"].fillna(_infer_season(df["date"])).astype(str)

    # Odds below 1.01 are data errors; drop them rather than poison the market model.
    for col in ("odds_home", "odds_draw", "odds_away"):
        df.loc[df[col] < 1.01, col] = np.nan

    df = df[CANONICAL_COLUMNS].sort_values(["date", "home_team"], kind="mergesort")
    return df.reset_index(drop=True)


def load_matches(paths: str | Path | Iterable[str | Path], dayfirst: bool = True) -> pd.DataFrame:
    """Load one or many CSV files and return a single canonical, date-sorted table."""
    if isinstance(paths, (str, Path)):
        paths = [paths]
    frames = []
    for p in paths:
        p = Path(p)
        files = sorted(p.glob("*.csv")) if p.is_dir() else [p]
        for f in files:
            frames.append(pd.read_csv(f, encoding_errors="replace"))
    if not frames:
        raise FileNotFoundError(f"no CSV files found in {paths!r}")
    return standardize(pd.concat(frames, ignore_index=True), dayfirst=dayfirst)


def download_football_data(league: str, seasons: Iterable[str], out_dir: str | Path) -> list[Path]:
    """Download season CSVs from football-data.co.uk.

    ``league`` is the site's code (``E0`` Premier League, ``E1`` Championship,
    ``SP1`` La Liga, ``D1`` Bundesliga, ``I1`` Serie A, ``F1`` Ligue 1, ...).
    ``seasons`` use the site's four digit codes, e.g. ``"2324"`` for 2023-24.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for season in seasons:
        url = FOOTBALL_DATA_URL.format(season=season, league=league)
        with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310 - fixed https host
            raw = resp.read()
        df = pd.read_csv(io.BytesIO(raw), encoding_errors="replace")
        start = 2000 + int(season[:2])
        df["Season"] = f"{start}-{season[2:]}"
        path = out_dir / f"{league}_{season}.csv"
        df.to_csv(path, index=False)
        written.append(path)
    return written


def played(df: pd.DataFrame) -> pd.DataFrame:
    """Rows with a final score."""
    return df.dropna(subset=["home_goals", "away_goals"]).reset_index(drop=True)


def outcome(home_goals, away_goals) -> np.ndarray:
    """Encode results as 0 = home win, 1 = draw, 2 = away win."""
    hg, ag = np.asarray(home_goals), np.asarray(away_goals)
    return np.where(hg > ag, 0, np.where(hg == ag, 1, 2))


def implied_probabilities(odds: np.ndarray, method: str = "power") -> np.ndarray:
    """Turn decimal 1X2 odds (n x 3) into probabilities with the margin removed.

    ``method="basic"`` divides by the overround. ``method="power"`` finds k with
    sum(p_i ** k) = 1 where p_i = 1/odds_i, which removes more margin from long
    shots and corrects most of the favourite-longshot bias.
    Rows with missing odds come back as NaN.
    """
    odds = np.asarray(odds, dtype=float)
    raw = 1.0 / odds
    if method == "basic":
        return raw / raw.sum(axis=1, keepdims=True)
    if method != "power":
        raise ValueError("method must be 'basic' or 'power'")
    out = np.full_like(raw, np.nan)
    ok = np.isfinite(raw).all(axis=1)
    r = raw[ok]
    lo, hi = np.full(len(r), 0.5), np.full(len(r), 3.0)
    for _ in range(60):  # bisection on k, vectorised over rows
        k = (lo + hi) / 2
        s = (r ** k[:, None]).sum(axis=1)
        too_big = s > 1
        lo = np.where(too_big, k, lo)
        hi = np.where(too_big, hi, k)
    k = (lo + hi) / 2
    p = r ** k[:, None]
    out[ok] = p / p.sum(axis=1, keepdims=True)
    return out


# --------------------------------------------------------------------------- #
# Synthetic league generator
# --------------------------------------------------------------------------- #
@dataclass
class SyntheticLeague:
    """Ground truth used to generate a synthetic league (handy for testing)."""

    teams: list[str]
    attack: dict[str, dict[str, float]]  # season -> team -> attack
    defence: dict[str, dict[str, float]]  # season -> team -> defence weakness
    home_advantage: float
    intercept: float
    rho: float


def _dc_sample(lam: float, mu: float, rho: float, rng: np.random.Generator, max_goals: int = 10):
    """Draw one score from the Dixon-Coles distribution."""
    m = score_matrix(lam, mu, rho, max_goals)
    idx = rng.choice(m.size, p=m.ravel())
    return divmod(int(idx), max_goals + 1)


def generate_synthetic_league(
    n_teams: int = 20,
    n_seasons: int = 5,
    start_year: int = 2019,
    seed: int = 7,
    home_advantage: float = 0.25,
    intercept: float = 0.15,
    rho: float = -0.08,
    bookmaker_margin: float = 0.05,
    strength_drift: float = 0.08,
) -> tuple[pd.DataFrame, SyntheticLeague]:
    """Simulate a double round-robin league with realistic structure.

    Team strengths follow a random walk between seasons (and drift slightly
    within a season), goals follow a Dixon-Coles bivariate Poisson, shots are
    generated from the expected goals, and bookmaker odds are derived from the
    true probabilities plus noise and a margin. The returned data looks like a
    real football-data.co.uk export, so the whole pipeline can be exercised
    offline and its estimates checked against known truth.
    """
    rng = np.random.default_rng(seed)
    teams = [f"Team {chr(65 + i // 26) if i >= 26 else ''}{chr(65 + i % 26)}" for i in range(n_teams)]
    att = rng.normal(0, 0.30, n_teams)
    dfn = rng.normal(0, 0.25, n_teams)
    att -= att.mean()
    dfn -= dfn.mean()

    rows = []
    truth_att, truth_def = {}, {}
    for s in range(n_seasons):
        year = start_year + s
        season = f"{year}-{str(year + 1)[-2:]}"
        if s > 0:
            att = att + rng.normal(0, strength_drift, n_teams)
            dfn = dfn + rng.normal(0, strength_drift, n_teams)
            att -= att.mean()
            dfn -= dfn.mean()
        truth_att[season] = dict(zip(teams, att.round(4)))
        truth_def[season] = dict(zip(teams, dfn.round(4)))

        # Circle-method schedule: 2*(n-1) rounds, one round per week.
        order = list(range(n_teams))
        rounds = []
        for r in range(n_teams - 1):
            pairs = [(order[i], order[n_teams - 1 - i]) for i in range(n_teams // 2)]
            pairs = [(a, b) if (r + i) % 2 == 0 else (b, a) for i, (a, b) in enumerate(pairs)]
            rounds.append(pairs)
            order = [order[0]] + [order[-1]] + order[1:-1]
        rounds += [[(b, a) for a, b in rnd] for rnd in rounds]
        rng.shuffle(rounds)

        season_start = pd.Timestamp(f"{year}-08-10")
        a_cur, d_cur = att.copy(), dfn.copy()
        for r_idx, rnd in enumerate(rounds):
            # Small in-season drift so recency weighting matters.
            a_cur = a_cur + rng.normal(0, 0.012, n_teams)
            d_cur = d_cur + rng.normal(0, 0.012, n_teams)
            base_date = season_start + pd.Timedelta(days=7 * r_idx + (14 if r_idx > 18 else 0))
            for h, a in rnd:
                date = base_date + pd.Timedelta(days=int(rng.integers(0, 3)))
                lam = np.exp(intercept + home_advantage + a_cur[h] + d_cur[a])
                mu = np.exp(intercept + a_cur[a] + d_cur[h])
                hg, ag = _dc_sample(lam, mu, rho, rng)

                # True 1X2 probabilities -> noisy bookmaker odds with margin.
                p = outcome_probs(score_matrix(lam, mu, rho))
                p_book = p * np.exp(rng.normal(0, 0.06, 3))
                p_book = p_book / p_book.sum() * (1 + bookmaker_margin)
                odds = np.round(1 / p_book, 2)

                shots_h = rng.poisson(lam * 8.5 + 3)
                shots_a = rng.poisson(mu * 8.5 + 3)
                sot_h = min(shots_h, max(hg, rng.binomial(shots_h, 0.35)))
                sot_a = min(shots_a, max(ag, rng.binomial(shots_a, 0.35)))
                rows.append(
                    {
                        "date": date,
                        "season": season,
                        "home_team": teams[h],
                        "away_team": teams[a],
                        "home_goals": hg,
                        "away_goals": ag,
                        "home_shots": shots_h,
                        "away_shots": shots_a,
                        "home_sot": sot_h,
                        "away_sot": sot_a,
                        "odds_home": odds[0],
                        "odds_draw": odds[1],
                        "odds_away": odds[2],
                    }
                )
        att, dfn = a_cur - a_cur.mean(), d_cur - d_cur.mean()

    df = standardize(pd.DataFrame(rows))
    truth = SyntheticLeague(teams, truth_att, truth_def, home_advantage, intercept, rho)
    return df, truth
