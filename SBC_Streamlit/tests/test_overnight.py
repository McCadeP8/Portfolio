from __future__ import annotations

import contextlib
import io
import json
import unittest
from datetime import date

from sbc_backend.jobs.overnight import main
from sbc_backend.fantrax_rotation import RotationPeriod, planned_post_kinds, simulated_today


class OvernightTests(unittest.TestCase):
    def test_dry_run_resolves_without_network(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["--dry-run", "--date", "2026-07-30", "--jobs", "validate"])
        self.assertEqual(status, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["nba_season"], "2026-27")
        self.assertEqual(payload["jobs"], ["validate"])

    def test_simulated_date_tracks_168_days_behind(self):
        self.assertEqual(simulated_today(date(2026, 8, 6)), date(2026, 2, 19))

    def test_opening_morning_rotation(self):
        period = RotationPeriod(2026, 34, date(2026, 2, 19), date(2026, 2, 20), date(2026, 2, 19))
        kinds = planned_post_kinds(period)
        self.assertIn("matchup_preview", kinds)
        self.assertIn("mobile_matchup_preview", kinds)
        self.assertIn("standings", kinds)
        self.assertNotIn("overnight_scores", kinds)
        self.assertIn("matchup_recap", kinds)
        self.assertEqual(
            planned_post_kinds(period, "opening"),
            ["matchup_preview", "mobile_matchup_preview", "standings", "mobile_standings"],
        )
        self.assertEqual(
            planned_post_kinds(period, "overnight"),
            ["matchup_recap", "mobile_matchup_recap", "record_leader"],
        )

    def test_middle_morning_rotation(self):
        period = RotationPeriod(2026, 34, date(2026, 2, 19), date(2026, 2, 20), date(2026, 2, 20))
        kinds = planned_post_kinds(period)
        self.assertEqual(
            kinds,
            ["overnight_scores", "mobile_overnight_scores", "matchup_recap", "mobile_matchup_recap", "record_leader"],
        )


if __name__ == "__main__":
    unittest.main()
