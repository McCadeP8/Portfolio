"""Every draft pick (30 teams x 2 rounds x 7 drafts) must appear on the league
pick pages exactly once and on the team page of every team that holds it."""
from __future__ import annotations

import unittest

import pandas as pd

import functions as f
from data import team_info


def _key(frame: pd.DataFrame) -> set[tuple]:
    return set(zip(frame["Year"].astype(str), frame["Round"].astype(str), frame["OGTeam"].astype(str)))


class DraftPickCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.picks = f.get_draft_picks()
        except Exception as exc:  # network or sheet outage
            raise unittest.SkipTest(f"draft picks unavailable: {exc}")
        if cls.picks is None or cls.picks.empty:
            raise unittest.SkipTest("draft picks unavailable")

    def test_every_team_round_and_draft_is_listed(self):
        years = sorted(self.picks["Year"].astype(int).unique())
        self.assertEqual(len(years), 7)
        for year in years:
            for round_name in ("1st Round", "2nd Round"):
                rows = self.picks[(self.picks["Year"].astype(int) == year) & (self.picks["Round"] == round_name)]
                self.assertEqual(set(rows["OGTeam"]), set(team_info), (year, round_name))
                self.assertEqual(len(rows), len(team_info), (year, round_name))

    def test_league_pages_show_every_pick_exactly_once(self):
        buckets = {
            "full": f.all_full_draft_picks, "swap": f.all_swap_draft_picks,
            "split": f.all_split_draft_picks, "locked": f.all_locked_draft_picks,
        }
        seen = {}
        for name, build in buckets.items():
            for key in _key(build(self.picks.copy())):
                self.assertNotIn(key, seen, f"{key} is on both {seen.get(key)} and {name}")
                seen[key] = name
        missing = _key(self.picks) - set(seen)
        self.assertFalse(missing, f"picks on no league page: {sorted(missing)}")

    def test_team_pages_show_every_pick_for_each_holder(self):
        builders = (f.full_draft_picks, f.swap_draft_picks, f.split_draft_picks, f.locked_draft_picks)
        for team in team_info:
            shown = set()
            for build in builders:
                shown |= _key(build(self.picks.copy(), team))
            held = self.picks[self.picks["CurrentTeam"].astype(str).str.split(",").map(lambda owners: team in [o.strip() for o in owners])]
            missing = _key(held) - shown
            self.assertFalse(missing, f"{team} holds but does not show {sorted(missing)}")


if __name__ == "__main__":
    unittest.main()
