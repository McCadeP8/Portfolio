# Input formats

## Fantrax

`fetch-fantrax` reads the league's public roster, NBA player catalog, and league matchup responses. Every JSON response is saved unchanged before normalization. A private session cookie is not stored or required for the currently configured endpoints.

## Scoring categories

Populate `config/categories.csv` with exactly these columns:

```csv
category,weight,direction
PTS,3,higher
```

The 13 configured categories are the SBC values confirmed by the user and total 413. `direction` describes whether higher or lower wins; turnovers are the sole lower-is-better category.

## Projections

Supply a CSV, TSV/text table, Excel workbook, or saved HTML page. A player-name column is required. Common provider headings such as `Player`, `Team`, `Pos`, `GP`, `MIN`, `FGM`, `FGA`, `FTM`, `FTA`, `3PM`, `PTS`, `REB`, `AST`, `STL`, `BLK`, and `TO` are recognized case-insensitively.

The configured Google Sheet tab can be refreshed directly with:

```powershell
fantasy-basketball import-google-projections
```

Repeated header rows are discarded. Shooting cells formatted like `0.573(754.6/1317.6)` are split into percentage, makes, and attempts. The importer derives `two_m = fg_m - three_m`, `two_a = fg_a - three_a`, and `ts_pct = points / (2 * (fg_a + 0.44 * ft_a))`. Plus/minus remains missing until a separate source is added.

Percentages alone are not used to reconstruct shooting volume. Makes and attempts remain separate so downstream aggregation can calculate percentages correctly.

## Manual identity overrides

Add reviewed aliases to `config/player_aliases.csv`:

```csv
source_name,canonical_name
Alex Sarr,Alexandre Sarr
```

Fuzzy matches are written to `data/processed/player_match_exceptions.csv` as suggestions and are never accepted automatically.

