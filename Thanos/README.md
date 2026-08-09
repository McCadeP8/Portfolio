# Thanos League · Year 8

A seeded, two-universe fantasy-football draft experience built with Streamlit.

## Run locally

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

Every visitor sees the same split because all eight snaps are derived from the fixed seed in `app.py`.

## Live Google Sheets

The app reads both public tabs directly and refreshes cached data every 15 seconds:

- Draft tab (`gid=1410253704`): `Draft, Round, Pick, Player`
- Randomization tab (`gid=1215542528`): `Type, Name`

Use `Team` in the `Type` column for the 16 fantasy teams. Position types are `QB`, `RB`, `WR`, `TE`, `K`, and `DST`. Drafted-player positions are inferred by matching `Player` against this tab, and each drafting team is inferred from `Draft`, `Round`, and `Pick` using the seeded snake order.

The `Draft` field assigns a recorded selection to `Alive` or `Dusted`. If that column is blank, the app assigns picks to a board using the team's seeded universe. If either Sheet cannot be reached or fails validation, the app stays usable with deterministic demo data and clearly labels the fallback.

## Player images

`player_images.csv` is the verified NFL/PFR headshot mapping reused from the NCFL app. Names are normalized for punctuation and spacing before matching. Players without a mapped image receive a built-in silhouette.

## Expected draft columns

`Draft, Round, Pick, Player`
