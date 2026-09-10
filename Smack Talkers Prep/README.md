# Smack Talkers Draft Simulator

A polished solo Streamlit rules lab for playing the seven stages slowly, replaying seeded games, and running bulk simulations.

## Run

```powershell
python -m pip install -r ..\requirements.txt
streamlit run app.py
```

Use **Start a new game** to replay endlessly. Reuse a random seed when you want the same sequence of draws.

The Second Quarter sign deck is modeled as 12 cards total: three each of MIN, MAX, ABS, and SUM.

## Yahoo 2026 Tuesday refresh

The two Yahoo league URLs are configured in `data/yahoo_2026/leagues.csv`. Refresh the
current game key, teams, and current-week scoreboards with:

```powershell
python refresh_yahoo_2026.py
```

The updater derives Yahoo's current NFL game key automatically, stores a raw JSON cache
under `data/yahoo_2026/raw`, and writes normalized status, teams, and matchup parquet files
under `data/yahoo_2026/processed`. The Streamlit app displays the latest cached update.
