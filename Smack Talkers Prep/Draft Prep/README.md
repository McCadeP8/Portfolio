# Smack Talkers Draft Prep

This folder contains the historical inputs and analysis-ready data for the
Smack Talkers snake and auction draft preparation project.

## Structure

- `data/raw/`: preserved CSV exports, renamed by inferred season and draft type.
- `data/processed/smack_talkers_draft_history.parquet`: all six drafts in one table.
- `data/raw/espn/`: preserved ESPN PPR Top 300 PDF cheat sheets.
- `data/processed/espn_ppr300_rankings.parquet`: 1,200 extracted ESPN rankings for 2023-2026.
- `data/processed/draft_history_with_espn.parquet`: league selections enriched with ESPN market data.
- `data/processed/team_owner_mapping.csv`: team-name list for manually linking aliases to owners.
- `scripts/build_draft_history.py`: reproducible normalization and validation script.
- `scripts/build_espn_rankings.py`: reproducible PDF extraction and league-history join.
- `data/raw/yahoo/<season>_<league_id>/`: checkpointed Yahoo source data and page snapshots.
- `data/processed/yahoo/<season>_<league_id>/`: normalized Yahoo teams, standings,
  scores, matchups, and available lineup data.
- `data/processed/yahoo/league_inventory.csv`: resumable extraction-status ledger for
  every supplied Yahoo league-season.
- `scripts/build_yahoo_history.py`: owner matching and Yahoo normalization pipeline.
- `app.py`: NCFL-inspired Streamlit league-history dashboard.
- `history_metrics.py`: tested lineup optimization, draft-retention, and all-play metrics.

## Important assumptions

- The source exports do not contain a season field. The no-suffix downloads were
  identified as 2025, `(1)` as 2024, and `(2)` as 2023 from their player pools.
- Excel shortened picks ending in zero (for example, `1.10` to `1.1`). The clean
  `round_pick` and `pick_in_round` fields are reconstructed from row order.
- The 2023 and 2024 auction drafts had 10 teams. The 2025 auction draft and all
  three snake drafts had 12 teams.
- `amount` is retained as exported: auction values are dollars and snake values are zero.
- `PK` is normalized to `K` in `position`; original values remain in `source_position`.
- ESPN defenses are matched to league defenses by season and normalized NFL-team abbreviation;
  other players are matched by season and normalized player name.
- Yahoo team names are treated as display labels. Cross-season identity uses the Yahoo
  team ID within a league-season and the canonical owner across seasons.

## Yahoo extraction status

- 2025 snake (`866885`): all 216 team-week lineup pages, 180 regular-season team
  scores, 90 matchups, and one-to-one owner mapping complete.
- 2025 auction (`724433`): all 216 team-week lineup pages, 180 regular-season team
  scores, 90 matchups, and one-to-one owner mapping complete.
- 2024 auction (`608509`): all 180 team-week lineup pages and owner mapping complete.
  Yahoo's schedule tables expose 14 rows per team, while final records and
  points-for include one additional scoring week. The difference is retained in
  `non_h2h_scoring_points` rather than silently discarded.
- 2024 snake (`748838`): all 216 team-week lineup pages and owner mapping complete.
  Yahoo's schedule tables expose 13 rows per team, while final records and
  points-for include two additional scoring weeks; those differences are retained as
  `non_h2h_scoring_points`.
- 2023 snake (`727134`): all 216 team-week lineup pages, 180 regular-season team
  scores, 90 matchups, and one-to-one owner mapping complete.
- 2023 auction (`773070`): all 180 team-week lineup pages, 150 regular-season team
  scores, 75 matchups, and one-to-one owner mapping complete.

## Rebuild

Install the shared dependencies from this project directory, then run:

```powershell
python -m pip install -r ..\requirements.txt
```

```powershell
python "Draft Prep/scripts/build_draft_history.py"
```

## Run the league-history app

```powershell
streamlit run "Draft Prep/app.py"
```

The history views are coverage-aware: complete schedule-score tables power the
league-strength analysis, while start/sit and roster-retention views use only
the detailed weekly lineup pages captured so far.

The Draft Room uses all six historical drafts. Snake roles are benchmarked by
round within each league-year; auction roles are benchmarked by dollars within
each league-year. Individual-player reaches and discounts use the archived ESPN
rank or auction value, while outcome charts only include Yahoo seasons with
captured standings.
