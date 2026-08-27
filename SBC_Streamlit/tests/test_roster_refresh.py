from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from big_data import _configured_roster_periods, _merge_roster_snapshots
from functions import _apply_official_2027_periods


ROOT = Path(__file__).resolve().parents[1]


class RosterRefreshTests(unittest.TestCase):
    def test_2027_matchup_calendar_uses_official_period_boundaries(self):
        calendar = pd.read_parquet(ROOT / "data_snapshots" / "period_calendar.parquet")
        current = calendar[calendar["Year"].eq(2027)].copy()
        current["Date"] = pd.to_datetime(current["Date"])

        regular = current[current["Period"].between(1, 36)]
        expected = {
            1: ("2026-10-20", "2026-10-23"),
            14: ("2026-12-03", "2026-12-08"),
            15: ("2026-12-09", "2026-12-13"),
            16: ("2026-12-14", "2026-12-16"),
            34: ("2027-02-11", "2027-02-13"),
            35: ("2027-02-14", "2027-02-16"),
            36: ("2027-02-17", "2027-02-25"),
        }
        boundaries = regular.groupby("Period")["Date"].agg(["min", "max"])
        for period, (start, end) in expected.items():
            self.assertEqual(boundaries.loc[period, "min"], pd.Timestamp(start))
            self.assertEqual(boundaries.loc[period, "max"], pd.Timestamp(end))

        postseason = current[current["Period"].between(37, 42)]
        self.assertEqual(len(postseason), 34)
        self.assertEqual(postseason["Date"].min(), pd.Timestamp("2027-02-26"))
        self.assertEqual(postseason["Date"].max(), pd.Timestamp("2027-03-31"))

    def test_official_period_override_preserves_postseason(self):
        calendar = pd.DataFrame(
            [
                {"Day": 48, "Year": 2027, "Date": "2026-12-06", "Period": 15, "Season": "Regular"},
                {"Day": 127, "Year": 2027, "Date": "2027-02-23", "Period": 36, "Season": "Regular"},
                {"Day": 130, "Year": 2027, "Date": "2027-02-26", "Period": 37, "Season": "Play-In"},
            ]
        )

        result = _apply_official_2027_periods(calendar)

        self.assertEqual(result["Period"].tolist(), [14, 36, 37])
        self.assertEqual(result["Season"].tolist(), ["Regular", "Regular", "Play-In"])

    def test_2027_calendar_covers_every_day_inclusively(self):
        periods = _configured_roster_periods(2027)

        self.assertEqual(len(periods), 174)
        self.assertEqual(periods.iloc[0]["games"], 1)
        self.assertEqual(periods.iloc[-1]["games"], 174)
        self.assertEqual(str(periods.iloc[0]["Date"]), "2026-10-20")
        self.assertEqual(str(periods.iloc[-1]["Date"]), "2027-04-11")

    def test_refresh_replaces_successful_period_and_preserves_everything_else(self):
        history = pd.DataFrame(
            [
                {"Year": 2026, "period": 1, "team_name": "Vegas", "id": "legacy"},
                {"Year": 2027, "period": 1, "team_name": "Vegas", "id": "old"},
                {"Year": 2027, "period": 2, "team_name": "Vegas", "id": "keep"},
            ]
        )
        fresh = pd.DataFrame(
            [
                {"Year": 2027, "period": 1, "team_name": "Vegas", "id": "new"},
                {"Year": 2027, "period": 1, "team_name": "Boise", "id": "new-two"},
            ]
        )

        result = _merge_roster_snapshots(history, fresh, 2027, {1})

        keys = set(result[["Year", "period", "team_name", "id"]].itertuples(index=False, name=None))
        self.assertIn((2026, 1, "Vegas", "legacy"), keys)
        self.assertIn((2027, 2, "Vegas", "keep"), keys)
        self.assertIn((2027, 1, "Vegas", "new"), keys)
        self.assertNotIn((2027, 1, "Vegas", "old"), keys)


if __name__ == "__main__":
    unittest.main()
