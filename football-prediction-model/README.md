# Football Match Prediction Model

A complete Python toolkit for forecasting football (soccer) matches. It combines
three different model families into a learned ensemble, prices every common betting
market from one consistent score distribution, evaluates itself with leak-free
walk-forward backtests, and simulates whole seasons with Monte Carlo.

```
                   ┌────────────────────┐
results CSV ──────►│ data.py            │  football-data.co.uk or canonical columns,
(+ odds, shots)    │ load / standardise │  odds -> margin-free probabilities
                   └─────────┬──────────┘
                             │  replayed in date order (no look-ahead)
        ┌────────────────────┼─────────────────────────┐
        ▼                    ▼                         ▼
┌───────────────┐   ┌──────────────────┐   ┌────────────────────────┐
│ Dixon-Coles   │   │ Elo ratings      │   │ FeatureBuilder (~70)   │
│ time-weighted │   │ + ordered logit  │   │ form, venue, EWM shots,│
│ bivariate     │   │                  │   │ season, rest, h2h, Elo │
│ Poisson       │   │                  │   │  -> logistic / GBM     │
└──────┬────────┘   └────────┬─────────┘   └───────────┬────────────┘
       │ P(H,D,A) + score    │ P(H,D,A)                │ P(H,D,A)
       │ matrix              ▼                         ▼
       │            ┌────────────────────────────────────────┐
       │            │ Ensemble: weights fitted on            │ (+ optional
       │            │ out-of-sample forecasts only           │  market member)
       │            └───────────────────┬────────────────────┘
       ▼                                ▼
┌──────────────────────────────────────────────────────────────┐
│ Score matrix rescaled to the ensemble 1X2 -> every market:   │
│ 1X2, double chance, draw-no-bet, totals, BTTS, clean sheets, │
│ Asian handicap (incl. quarter lines), correct score, xG      │
└───────────────┬───────────────────────────────┬──────────────┘
                ▼                               ▼
     backtest.py: walk-forward,       simulation.py: Monte Carlo
     log loss / Brier / RPS,          final tables, title / top-4 /
     calibration, value betting       relegation probabilities
```

## Quick start

```bash
cd football-prediction-model
pip install -r requirements.txt
python -m football_predictor demo
```

The demo needs no internet. It generates a synthetic 20-team league with known
true team strengths, backtests every model, shows that the fitted parameters
recover the truth, prints a full match report and projects a season from its
midpoint.

### Using real data

[football-data.co.uk](https://www.football-data.co.uk/data.php) publishes free
results, shots and bookmaker odds for over 20 leagues. Either download the CSVs
yourself or let the tool fetch them:

```bash
# Premier League, last five seasons
python -m football_predictor download --league E0 --seasons 2021 2122 2223 2324 2425 --out data/E0
```

League codes: `E0` Premier League, `E1` Championship, `SP1` La Liga, `D1`
Bundesliga, `I1` Serie A, `F1` Ligue 1, `N1` Eredivisie, `P1` Primeira Liga, and
others listed on the site. Any CSV with `date, home_team, away_team, home_goals,
away_goals` columns also works (shots and odds are optional).

## Commands

| command | what it does |
|---|---|
| `demo` | end-to-end run on synthetic data |
| `generate --out FILE` | write a synthetic league CSV |
| `download --league E0 --seasons 2324 2425` | fetch football-data.co.uk files |
| `backtest --data PATH [--plots DIR] [--out FILE]` | walk-forward evaluation, calibration, betting simulation, charts |
| `predict --data PATH --home X --away Y [--odds H D A] [--json]` | full report for one match |
| `predict --data PATH --fixtures FILE [--out FILE]` | forecasts for a list of fixtures |
| `ratings --data PATH` | current Dixon-Coles and Elo ratings |
| `simulate --data PATH [--fixtures FILE] [--sims N]` | Monte Carlo final table |
| `tune --data PATH` | choose the Dixon-Coles time-decay rate by out-of-sample log loss |

Shared options: `--ml logistic|gbm` picks the ML model, `--xi` sets the time
decay, `--with-market` adds bookmaker odds to the ensemble, and
`--market-features` gives the odds to the ML model as inputs.

Example:

```bash
python -m football_predictor predict --data data/E0 --home Arsenal --away Chelsea --odds 1.85 3.8 4.2
```

prints a report like this (abridged, from the synthetic data):

```
  Team A vs Team G   (2024-05-12)
  Prediction: Home win

  1X2            prob    fair odds
  home        45.8%      2.19
  draw        30.6%      3.27
  away        23.7%      4.22

  Expected goals: 1.00 - 0.65   most likely score 1-0

  Model components    home    draw    away   weight
  dixon_coles       36.0%  38.0%  26.0%    0.53
  elo               49.1%  26.5%  24.4%    0.03
  ml                57.6%  21.7%  20.7%    0.43

  Totals          over    under
    2.5 goals   22.8%   77.2%
  Both teams to score: yes  29.0%  no  71.0%

  Asian handicap (home)   win  half-win  push  half-loss  loss   fair
   -0.25             45.8%   0.0%   0.0%   30.6%  23.7%   1.85

  Value vs offered odds     odds   market   model    edge
  draw                     3.50    27.1%   30.6%   +7.0%  <-- value
```

## Python API

```python
from football_predictor import FootballPredictor, PredictorConfig, load_matches, walk_forward, simulate_season

matches = load_matches("data/E0")                 # a file, a folder, or a list of either

bt = walk_forward(matches, PredictorConfig())     # honest out-of-sample forecasts
bt.metrics()                                      # log loss, Brier, RPS, accuracy for every model
bt.calibration()                                  # reliability table
bt.betting(min_edge=0.05, staking="kelly").summary

model = FootballPredictor().fit(matches)
model.predict_match("Arsenal", "Chelsea", odds=(1.85, 3.8, 4.2))   # dict with every market
model.predict(fixtures_df)                        # DataFrame, one row per fixture
model.dc.ratings_table()                          # attack / defence ratings
```

`examples/quickstart.py` runs through all of it.

## The models

### 1. Dixon-Coles (`dixon_coles.py`)

Goals scored by each side are Poisson, with rates set by attack strength, the
opponent's defensive weakness and home advantage:

```
home goals ~ Poisson(λ),  log λ = c + h + attack[home] + defence[away]
away goals ~ Poisson(μ),  log μ = c     + attack[away] + defence[home]
P(x, y)    = τ(x, y; λ, μ, ρ) · Pois(x; λ) · Pois(y; μ)
```

`τ` is the Dixon & Coles (1997) correction that adjusts the four low scores
(0-0, 1-0, 0-1, 1-1). Independent Poissons under-predict low-scoring draws, and
`ρ < 0` fixes that.

* **Time weighting.** Each match's log-likelihood is weighted by
  `exp(-ξ · days_ago)`, so the ratings follow form. The default ξ = 0.0019/day
  (a half-life of about a year) can be tuned with `tune`.
* **Fitting.** Maximum likelihood by L-BFGS-B with an **analytic gradient**,
  checked against finite differences in the tests, and warm starts between
  refits. A full refit takes about 20 ms, which is what makes the walk-forward
  backtest practical.
* **Regularisation.** A small ridge penalty shrinks teams with little data
  toward average. Teams never seen before (for example, promoted sides) take the
  average rating of the three weakest teams.
* **Output.** A full score matrix (0-10 goals each side). Every goal market
  comes from it.

### 2. Elo + ordered logit (`elo.py`)

World Football Elo-style ratings: K = 20, +65 points for home advantage, a
margin-of-victory multiplier (×1.5 for two goals, ×(11+GD)/8 for three or
more), 25 % regression to the mean between seasons, and promoted teams start
60 points below average. Elo only gives an expected score, so an **ordered
logistic regression** (`OrderedLogit`) learns how the rating gap maps to
P(home) / P(draw) / P(away). Because home win, draw and away win are ordered,
this captures that draws are most likely when the teams are evenly matched.

### 3. Feature-based ML model (`features.py`, `ml_model.py`)

`FeatureBuilder` replays the match history in date order. For each match it
reads every team's state *before* the match and only updates that state
afterwards. Matches on the same day never see each other's results. A test
checks this by tampering with future results and confirming earlier features
don't change.

| group | features (for home `h_`, away `a_`, and differences `d_`) |
|---|---|
| ratings | Elo before the match, Elo gap with home advantage, Elo expected score |
| form | points per game, goals for and against over the last 3 / 5 / 10 matches |
| venue form | the home side's recent home record and the away side's recent away record |
| exponentially weighted | goals, shots and shots on target, for and against; conversion rate |
| matchup | own attack vs opponent's defence composite |
| season | points per game, goal difference per game, games played so far |
| schedule | rest days since the last match (capped at 21), experience |
| head to head | meetings, average goal difference, home win rate (last 6) |
| market *(optional)* | margin-free bookmaker probabilities |

Two estimators: a regularised multinomial **logistic regression** (default;
robust on a few seasons of data) or **histogram gradient boosting** (`--ml gbm`;
finds interactions but needs more data). Recent matches are up-weighted, with a
540-day half-life.

### 4. Ensemble (`ensemble.py`)

Linear (or logarithmic) pooling. The weights are constrained to be non-negative
and to sum to 1, and are chosen to minimise **log loss on out-of-sample
forecasts only**: the earlier blocks of a walk-forward run. Fitting weights on
in-sample forecasts would reward whichever model overfits most. The weights are
shrunk 10 % toward equal for stability. When a component can't produce a
forecast (for example, the market member when a fixture has no odds), the
remaining weights are renormalised.

### 5. Consistent markets (`markets.py`)

The Dixon-Coles score matrix is **rescaled so its 1X2 split matches the
ensemble**. The home-win, draw and away-win regions are each multiplied by a
constant, so the goal model still decides which scorelines make up each result.
Every market then comes from one distribution and agrees with the headline
probabilities: 1X2, double chance, draw-no-bet, over/under 0.5 to 4.5, BTTS,
clean sheets, team goals, Asian handicaps (whole, half and quarter lines, with
fair odds that account for pushes and half results) and correct scores.

Bookmaker odds are converted to probabilities with the **power method**: it
solves for k such that Σ(1/oᵢ)ᵏ = 1, which removes the margin unevenly in a way
that corrects most of the favourite-longshot bias. Simple normalisation is also
available.

## Evaluation (`evaluation.py`, `backtest.py`)

`walk_forward` splits the test period into blocks (default 14 days). Before each
block, every model is refitted on matches played strictly before it. Ensemble
weights come from earlier blocks' forecasts only. The ML model is refitted
every 28 days because it's the most expensive to fit.

Metrics:

* **RPS (ranked probability score)**: the standard football metric. It is
  Brier on the cumulative distribution, so calling a draw when the home side
  wins counts as a smaller error than calling an away win.
* **Log loss**, **multi-class Brier score**, **accuracy**.
* **Calibration table** with standard errors, and expected calibration error.
* **Benchmarks:** the base-rate forecast (always the historical H/D/A
  frequencies) and, when odds are present, the bookmaker's margin-free
  probabilities. A model that doesn't beat the base rate is useless. Beating
  the closing market is very hard.

`--plots DIR` saves a calibration curve, a rolling RPS chart for every model and
a bankroll curve.

### Results on the bundled synthetic league

Last two seasons (760 matches), forecast out of sample:

| model | log loss | Brier | RPS | accuracy |
|---|---|---|---|---|
| bookmaker (margin removed) | 0.966 | 0.574 | 0.194 | 55.5 % |
| ensemble incl. market, GBM | 0.972 | 0.578 | 0.196 | 54.6 % |
| Dixon-Coles | 0.979 | 0.583 | 0.198 | 52.5 % |
| ensemble (no market) | 0.982 | 0.585 | 0.199 | 52.2 % |
| Elo | 0.994 | 0.592 | 0.203 | 51.8 % |
| ML (logistic) | 1.001 | 0.597 | 0.203 | 50.8 % |
| base rate | 1.077 | 0.652 | 0.231 | 42.8 % |

Dixon-Coles recovers the true parameters: home advantage 0.217 against a true
0.25, ρ −0.095 against −0.08, and a 0.96 correlation with the true attack and
defence ratings. The ensemble is well calibrated. Two cautions about these
numbers:

* The synthetic data is *generated* by a Dixon-Coles process, so Dixon-Coles has
  a structural advantage here, and the synthetic bookmaker sees the true
  strengths plus noise, so it is very hard to beat. On real data the
  feature-based model usually earns a larger ensemble weight. For reference,
  good published models in top leagues reach an RPS of about 0.19–0.21.
* The betting simulation **loses money** on this data, which is the honest
  and typical result. Betting wherever the model disagrees with an efficient
  market mostly selects the model's own errors. Treat any profitable backtest
  with suspicion: check that the odds you tested against were available at
  the time, and expect bookmakers to limit winning accounts.

## Season simulation (`simulation.py`)

`simulate_season` plays out the remaining fixtures n times (10,000 by default),
sampling each scoreline from the ensemble-rescaled score matrix. It ranks teams
by points, then goal difference, then goals scored, then at random, and
reports expected points with a 10–90 % band, expected position, the full
finishing-position distribution, and title, top-4 and relegation probabilities
(zones are configurable). Projected from the midpoint of the synthetic
2023-24 season, it gave the eventual champion an 82 % title chance and its top
three matched the actual top three.

## Project layout

```
football-prediction-model/
├── football_predictor/
│   ├── data.py          loading, standardising, odds -> probabilities, synthetic league
│   ├── markets.py       score matrix, every market, Asian handicap, rescaling
│   ├── dixon_coles.py   time-weighted Dixon-Coles with analytic gradient, decay tuning
│   ├── elo.py           Elo ratings, ordered logit
│   ├── features.py      leak-free feature engineering
│   ├── ml_model.py      logistic regression / gradient boosting
│   ├── ensemble.py      out-of-sample weighted pooling
│   ├── predictor.py     FootballPredictor: fit / predict / predict_match
│   ├── backtest.py      walk-forward evaluation, betting simulation
│   ├── simulation.py    league table, Monte Carlo season projection
│   ├── evaluation.py    log loss, Brier, RPS, calibration
│   ├── reporting.py     text reports and charts
│   └── cli.py           command-line interface
├── data/synthetic_league.csv
├── examples/quickstart.py
└── tests/test_models.py
```

Run the tests with `python -m pytest`.

## Ideas for extending it

* **Expected goals (xG):** fit Dixon-Coles on xG instead of, or blended with,
  goals (sources: Understat, FBref). This is usually the biggest single
  improvement.
* **Team news:** injuries, suspensions and rotation before cup or European
  matches, added as features.
* **Bivariate Poisson / negative binomial** goal models to capture
  over-dispersion.
* **Pi-ratings** or **Glicko** as further rating components.
* **Closing-line value:** compare model prices with closing odds rather than
  opening odds. It is the most reliable sign of a real edge.
* **Hierarchical priors** for promoted teams, using their previous-season
  ratings in the lower division.

## References

* Dixon, M. J. & Coles, S. G. (1997). *Modelling association football scores
  and inefficiencies in the football betting market.* Applied Statistics 46(2).
* Maher, M. J. (1982). *Modelling association football scores.* Statistica
  Neerlandica 36(3).
* Constantinou, A. C. & Fenton, N. E. (2012). *Solving the problem of inadequate
  scoring rules for assessing probabilistic football forecast models.* JQAS 8(1).
* Hvattum, L. M. & Arntzen, H. (2010). *Using ELO ratings for match result
  prediction in association football.* IJF 26(3).
* Kelly, J. L. (1956). *A new interpretation of information rate.* Bell System
  Technical Journal.

*For research and education. Football is noisy: even the best models give the
favourite about a 50 % chance and are wrong roughly half the time.*
