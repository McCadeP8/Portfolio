from __future__ import annotations

import unittest

import pandas as pd

from big_data import _configured_roster_periods, _merge_roster_snapshots


class RosterRefreshTests(unittest.TestCase):
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
