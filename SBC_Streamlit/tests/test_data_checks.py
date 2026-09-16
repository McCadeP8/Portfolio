from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

import functions


def _pick(year: int, *, swap: bool = False, fully_owned: bool = False) -> dict:
    return {
        "Year": year,
        "Round": "1st Round",
        "OGTeam": "San Diego",
        "TeamTouched": None,
        "CurrentTeam": "El Paso",
        "PickSwap": swap,
        "FullyOwned": fully_owned,
        "TwoYearLimit": False,
        "Locked": False,
        "Explanation": None,
        "Notes": None,
    }


class StepienDataCheckTests(unittest.TestCase):
    def test_swap_counts_as_retaining_a_first_round_selection(self):
        picks = pd.DataFrame([
            _pick(2027, swap=True),
            _pick(2029, fully_owned=True),
        ])

        with patch.object(functions, "current_year", 2027):
            result = functions.stepien_data_check(picks)

        false_opening_gap = result[
            (result["Team"] == "El Paso")
            & (result["Year"] == 2026)
            & (result["Gap Closed"] == 2029)
        ]
        self.assertTrue(false_opening_gap.empty)

    def test_two_consecutive_drafts_without_a_first_are_flagged(self):
        picks = pd.DataFrame([_pick(2029, fully_owned=True)])

        with patch.object(functions, "current_year", 2027):
            result = functions.stepien_data_check(picks)

        el_paso = result[result["Team"] == "El Paso"]
        self.assertEqual(el_paso.iloc[0]["Year"], 2026)
        self.assertEqual(el_paso.iloc[0]["Gap Closed"], 2029)


class FantraxTranslationCheckTests(unittest.TestCase):
    def test_translation_does_not_require_a_current_roster_spot(self):
        cap_sheet = pd.DataFrame([{
            "Player": "Retired Example Jr.",
            "Trade.Restriction": "Retired",
        }])
        fantrax_players = pd.DataFrame([{
            "name": "Retired Example",
            "fantraxId": "old01",
        }])

        result = functions.fantrax_players_check(
            cap_sheet,
            fantrax_players,
            pd.DataFrame(),
        )

        self.assertTrue(result.empty)

    def test_only_truly_unknown_players_remain(self):
        cap_sheet = pd.DataFrame([
            {"Player": "Known Player", "Trade.Restriction": None},
            {"Player": "Unknown Prospect", "Trade.Restriction": None},
        ])
        fantrax_players = pd.DataFrame([{
            "name": "Known Player",
            "fantraxId": "known01",
        }])

        result = functions.fantrax_players_check(cap_sheet, fantrax_players, pd.DataFrame())

        self.assertEqual(result["Cap Sheet Name"].tolist(), ["Unknown Prospect"])

    def test_current_fantrax_identity_wins_over_historical_conflicts(self):
        current = pd.DataFrame([{
            "name": "Jalen Johnson",
            "fantraxId": "current-id",
        }])

        catalog = functions._fantrax_identity_catalog(current)

        jalen = catalog[catalog["_player_key"] == functions.normalize_player_key("Jalen Johnson")]
        self.assertEqual(jalen["fantraxId"].tolist(), ["current-id"])


if __name__ == "__main__":
    unittest.main()
