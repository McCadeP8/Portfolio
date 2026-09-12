# The Vampire Hunt

An atmospheric Streamlit home for The Vampire Hunt fantasy football league.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Fantrax player scores

Because the league is publicly viewable, the app pulls rosters, team totals, and
official weekly player FPts directly from Fantrax without login credentials. Player
scores are refreshed every minute or immediately with the Scoreboard refresh button.
