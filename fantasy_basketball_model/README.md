# Fantasy Basketball Analytics

This repository contains the Phase 1 data foundation for the 2026–27 fantasy basketball analytics project. It reuses the successful Fantrax acquisition pattern from the sibling `SBC_Streamlit` app while separating network ingestion, immutable raw snapshots, normalization, validation, player matching, and reporting.

The current Fantrax configuration identifies 30 teams and a 36-period regular-season schedule with two opponents per team per period. The authoritative 13 scoring categories total 413 points. The project also contains a frozen six-season SBCFBL history snapshot, cleaned external projections, and a saved NBA schedule used for league-level analysis.

The projection layer produces 0.00–10.00 team, player, category, and chemistry ratings. Chemistry is contextual: 5.00 is neutral, while values above or below 5.00 measure production gained or lost relative to portable talent.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,reports]"
```

## Run Phase 1

```powershell
fantasy-basketball fetch-fantrax
fantasy-basketball import-google-projections
fantasy-basketball import-projections "C:\path\to\hashtag-projections.html" --snapshot-date 2026-10-09
fantasy-basketball build
fantasy-basketball import-history --fetch-current-nba-schedule  # one-time snapshot only
pytest
quarto render reports/data_audit.qmd
```

See [docs/input_formats.md](docs/input_formats.md) before adding categories or projections.

## Outputs

- `data/raw/`: timestamped, unchanged source snapshots (ignored by Git)
- `data/processed/teams.csv`: stable Fantrax team IDs, names, and abbreviations
- `data/processed/rosters.csv`: current ownership, roster slot, and status
- `data/processed/schedule.csv`: one row per Fantrax matchup
- `data/processed/fantrax_players.csv`: NBA-wide Fantrax player identity catalog
- `data/processed/canonical_player_projections.csv`: roster/player/projection join
- `data/processed/player_match_exceptions.csv`: unresolved identity suggestions
- `data/processed/data_quality_issues.csv`: visible validation failures and warnings
- `data/processed/historical_matchups.parquet`: 2021–2026 matchup results joined to both teams' category statistics
- `data/processed/league_category_summary.csv`: category win alignment and historical winning benchmarks
- `data/processed/league_category_cowin.csv`: 13×13 category co-win matrix
- `data/processed/sbc_period_calendar.csv`: dated SBCFBL matchup-period calendar
- `data/processed/nba_schedule.csv`: saved 2020–21 through 2026–27 NBA schedule mapped to SBCFBL periods
- `data/processed/team_ratings.csv`: overall projected team strength, talent, and chemistry
- `data/processed/team_category_ratings.csv`: team Rating and Chemistry by category
- `data/processed/player_ratings.csv`: portable player Talent and current-team Chemistry
- `data/processed/player_category_ratings.csv`: player Talent by category
- `data/processed/player_team_fit.csv`: every projected player's overall fit on all 30 teams
- `data/processed/player_team_category_fit.csv`: category-level chemistry for projected players on all 30 teams
- `data/processed/counting_logistic_models.csv`: coefficients and diagnostics for the nine counting-category win models
- `data/processed/counting_logistic_curves.csv`: fitted 24.93-game probability curves
- `data/processed/counting_logistic_bins.csv`: observed calibration points used in the report visuals
- `data/processed/shooting_logistic_models.csv`: four volume-weighted points-gained win models
- `data/processed/shooting_logistic_curves.csv`: fitted shooting-category probability curves
- `data/processed/shooting_logistic_bins.csv`: observed shooting-model calibration points
- `data/processed/shooting_league_averages.csv`: attempt-weighted shooting baselines by season
- `data/processed/player_shooting_points_gained.csv`: four additive points-gained metrics for every projected player
- `config/nba_team_plus_minus.csv`: supplied NBA team projections used to allocate player +/- by projected minute share
- `data/processed/overall_logistic_model.csv`: diagnostics for the 13-input matchup-win model
- `data/processed/overall_logistic_coefficients.csv`: standardized conditional effects for all 13 categories
- `data/processed/overall_logistic_calibration.csv`: predicted and observed matchup-win calibration bands
- `data/processed/player_value_ratings.csv`: 13 replacement-player category ratings plus the 13-input Ovr rating

Build the rating outputs after rebuilding the canonical projection file:

```powershell
.\.venv\Scripts\python.exe -m fantasy_basketball.cli rate
```

Fit and print the nine standardized counting-category logistic regressions:

```powershell
.\.venv\Scripts\python.exe -m fantasy_basketball.cli fit-counting-models
```

Fit the four volume-weighted shooting-category regressions and write projected player points gained:

```powershell
.\.venv\Scripts\python.exe -m fantasy_basketball.cli fit-shooting-models
```

Fit the overall matchup-win model with all 13 category inputs:

```powershell
.\.venv\Scripts\python.exe -m fantasy_basketball.cli fit-overall-model
```

Build replacement-player category and overall ratings for every player with a projection. Minors receive portable player ratings but remain excluded from team aggregation:

```powershell
.\.venv\Scripts\python.exe -m fantasy_basketball.cli rate-player-value
```
- `reports/data_audit.qmd`: reproducible Quarto HTML audit

The history import is deliberately manual. The rendered report never calls SBC Streamlit, Fantrax, ESPN, or NBA.com for historical data; it reads the saved local snapshot so league-history results remain stable.

## Assumptions and unresolved inputs

- The configured league is the 2026–27 SBCFBL league used by the sibling app.
- Roster period 1 is the intended preseason/current snapshot. Pass `--period N` to choose another Fantrax period.
- Fantrax's league-info response defines matchup pairings but does not expose the scoring weights used by this project.
- The user confirmed that the sibling app's 13 category weights are authoritative and total 413.
- Hashtag Basketball projections must be supplied by the user as a saved/exported file. No authenticated page is scraped and no unofficial API is assumed.
- Player eligibility comes from the Fantrax NBA player catalog; assigned roster slots and active/reserve/minors status come from the league roster response.

Phase 1 deliberately excludes ratings, chemistry, clustering, optimization, and simulations.
