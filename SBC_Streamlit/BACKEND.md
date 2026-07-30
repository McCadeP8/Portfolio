# SBC backend operations

The Streamlit screens remain the presentation layer. `sbc_backend` now owns data locations, selective reads, resilient HTTP caching, validation, atomic writes, scheduled jobs, and the ESPN live-data boundary.

## Data flow

1. Sheet and Fantrax sources refresh the small league snapshots.
2. ESPN completed games update the canonical player-game archive.
3. Shot and play-by-play builders resume from checkpoints and update only the current season.
4. Matchup aggregates are rebuilt from canonical inputs.
5. Contracts are validated before a manifest and run report are published.

Every Parquet replacement is atomic. A failed download or transform leaves the last good file intact. The overnight job has a six-hour stale lock, per-job results, a `latest.json` report, and an optional Discord notification.

## Commands

```powershell
.\.venv\Scripts\python.exe -m sbc_backend.jobs.overnight --dry-run
.\.venv\Scripts\python.exe -m sbc_backend.jobs.overnight --strict
.\.venv\Scripts\python.exe -m sbc_backend.jobs.validate
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Use `--jobs validate`, or another ordered subset, for targeted operations. `--date` and `--lookback-days` make reruns deterministic.

## Live ESPN rollout

`SBC_LIVE_MODE` is the safety gate:

- `off`: no live polling; current production behavior.
- `shadow`: poll ESPN, normalize scores and player stats, and save observations under `.runtime/live`, but publish nothing to the UI.
- `live`: make normalized rows available to the presentation layer. The UI still needs an explicit consumer before users see live data.

Run shadow mode through preseason and compare its normalized rows with final box scores. Only set `live` after coverage, correction behavior, and ESPN rate tolerance are satisfactory.

## Hosting and storage

The included Dockerfile runs on Render, Railway, Fly.io, Azure Container Apps, AWS App Runner, or any container host. Large changing Parquet files should not keep growing the Git repository. The nightly workflow can publish them to S3-compatible storage such as Amazon S3, Cloudflare R2, Backblaze B2, or DigitalOcean Spaces.

Configure the workflow secrets named `SBC_DATA_BUCKET`, `SBC_DATA_ACCESS_KEY_ID`, `SBC_DATA_SECRET_ACCESS_KEY`, `SBC_DATA_REGION`, and optionally `SBC_DATA_ENDPOINT` and `SBC_DATA_PREFIX`. Expose the stored prefix through a CDN or public read-only URL, then set `SBC_DATA_BASE_URL` in the app. The repository prefers remote canonical data, caches it locally, falls back to the last cached copy during a transient outage, and discovers season archives from the published manifest.

Keep write credentials only in the scheduled job. The public app needs read-only HTTP access, never storage keys or the Discord webhook.

## Recovery

The `_runs/latest.json` report identifies the failed stage. Correct the source or code, rerun only that stage and its downstream stages, then run validation. Atomic promotion means no manual restoration is normally required; for a bad but valid publication, restore the prior object-store version and invalidate the CDN cache.
