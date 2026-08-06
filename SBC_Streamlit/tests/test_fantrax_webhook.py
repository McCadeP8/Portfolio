from __future__ import annotations

import unittest
from io import BytesIO
from unittest.mock import Mock, patch

import pandas as pd
import requests
from PIL import Image

from functions import build_live_scoreboard_image, build_mobile_live_scoreboard_image, build_mobile_matchup_preview_image, build_mobile_matchup_recap_image, build_mobile_standings_image, build_matchup_preview_image, build_matchup_recap_image, build_record_leader_announcement_image, build_standings_bracket_image, matchup_period_progress, post_fantrax_webhook


class FantraxWebhookTests(unittest.TestCase):
    @patch("functions.requests.post")
    def test_posts_fixed_message_as_webhook_content(self, mock_post):
        response = Mock(status_code=204)
        response.raise_for_status.return_value = None
        mock_post.return_value = response

        status_code = post_fantrax_webhook(
            "https://example.com/secret-webhook",
            "This is working",
        )

        self.assertEqual(status_code, 204)
        mock_post.assert_called_once_with(
            "https://example.com/secret-webhook",
            json={"content": "This is working"},
            timeout=15,
        )

    @patch("functions.requests.post")
    def test_rejects_non_https_url_before_posting(self, mock_post):
        with self.assertRaisesRegex(ValueError, "valid HTTPS webhook URL"):
            post_fantrax_webhook("http://example.com/webhook")

        mock_post.assert_not_called()

    @patch("functions.requests.post")
    def test_network_error_does_not_expose_webhook_url(self, mock_post):
        secret_url = "https://example.com/very-secret-token"
        mock_post.side_effect = requests.ConnectionError(f"Could not reach {secret_url}")

        with self.assertRaisesRegex(RuntimeError, "webhook could not be reached") as raised:
            post_fantrax_webhook(secret_url)

        self.assertNotIn(secret_url, str(raised.exception))

    @patch("functions.requests.post")
    def test_posts_scoreboard_as_png_attachment(self, mock_post):
        response = Mock(status_code=204)
        response.raise_for_status.return_value = None
        mock_post.return_value = response

        status_code = post_fantrax_webhook(
            "https://example.com/secret-webhook",
            message="",
            image_bytes=b"png-bytes",
            image_filename="scores.png",
        )

        self.assertEqual(status_code, 204)
        kwargs = mock_post.call_args.kwargs
        self.assertEqual(kwargs["data"]["payload_json"], '{"content": ""}')
        self.assertEqual(kwargs["files"]["files[0]"], ("scores.png", b"png-bytes", "image/png"))
        self.assertEqual(kwargs["timeout"], 30)

    def test_matchup_progress_uses_completed_calendar_days(self):
        calendar = pd.DataFrame({
            "Year": [2027] * 7,
            "Period": [1] * 7,
            "Date": pd.date_range("2026-10-20", periods=7),
        })

        self.assertEqual(matchup_period_progress(calendar, 2027, 1, "2026-10-19"), 0.0)
        self.assertEqual(matchup_period_progress(calendar, 2027, 1, "2026-10-22"), 42.9)
        self.assertEqual(matchup_period_progress(calendar, 2027, 1, "2026-10-27"), 100.0)

    def test_builds_one_png_row_per_matchup(self):
        scores = pd.DataFrame([
            {"TeamA": "Alpha", "TeamB": "Beta", "TeamA_Score": 250, "TeamB_Score": 163},
            {"TeamA": "Gamma", "TeamB": "Delta", "TeamA_Score": 201.5, "TeamB_Score": 211.5},
        ])

        result = build_live_scoreboard_image(scores, 42.9, "2026-27", "Period 1", "2026-10-22 08:00")
        rendered = Image.open(BytesIO(result))

        self.assertEqual(rendered.format, "PNG")
        self.assertEqual(rendered.size, (2000, 154 + 54 + 78 + 14 + 46))

    @patch("functions._scoreboard_logo_bytes", return_value=None)
    def test_builds_tall_mobile_scoreboard(self, _mock_logo):
        scores = pd.DataFrame([
            {"TeamA": "Alpha", "TeamB": "Beta", "TeamA_Score": 250, "TeamB_Score": 163},
            {"TeamA": "Gamma", "TeamB": "Delta", "TeamA_Score": 201.5, "TeamB_Score": 211.5},
        ])

        result = build_mobile_live_scoreboard_image(scores, 100, "2026-27", "Oct 20-Oct 26", "2026-10-27 08:00")
        rendered = Image.open(BytesIO(result))

        self.assertEqual(rendered.format, "PNG")
        self.assertEqual(rendered.size, (1080, 176 + 52 + 2 * 112 + 14 + 48))

    @patch("functions._scoreboard_logo_bytes", return_value=None)
    def test_non_regular_sections_reserve_west_and_east_columns(self, _mock_logo):
        scores = pd.DataFrame([
            {"Type": "Playoffs", "TeamA": "Albuquerque", "TeamB": "Anaheim", "TeamA_Score": 250, "TeamB_Score": 163},
            {"Type": "Playoffs", "TeamA": "Anchorage", "TeamB": "Austin", "TeamA_Score": 220, "TeamB_Score": 193},
            {"Type": "Playoffs", "TeamA": "Boise", "TeamB": "San Diego", "TeamA_Score": 180, "TeamB_Score": 233},
            {"Type": "Playoffs", "TeamA": "Baltimore", "TeamB": "Buffalo", "TeamA_Score": 205, "TeamB_Score": 208},
        ])

        result = build_live_scoreboard_image(scores, 100, "2026-27", "Playoffs", "2027-04-01 08:00")
        rendered = Image.open(BytesIO(result))

        # Three West games require three rows even though the East has only one.
        self.assertEqual(rendered.size, (2000, 154 + 54 + 3 * 78 + 14 + 46))

    @patch("functions._scoreboard_logo_bytes", return_value=None)
    def test_builds_matchup_recap_one_pager(self, _mock_logo):
        matchup = {
            "Year": 2026,
            "Period": 14,
            "Type": "Regular Season",
            "Round": "Regular",
            "TeamA": "Vegas",
            "TeamB": "Baltimore",
            "TeamA_Score": 253.5,
            "TeamB_Score": 159.5,
        }
        category_rows = []
        for category in ["MP", "TS%", "2PT%", "3PT%", "FT%", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]:
            category_rows.append({"Category": category, "Vegas": 10, "Baltimore": 8, "Winner": "Tie" if category == "FT%" else "Vegas"})
        players = pd.DataFrame([
            {"sbc_team": "Vegas", "display_player": "Player One", "GP": 3, "MP": 90, "PTS": 70, "OREB": 3, "DREB": 15, "AST": 12, "ST": 4, "BLK": 2, "TO": 5, "TS%": .61, "2PTM": 20, "2PTA": 35, "2PT%": .571, "3PTM": 8, "3PTA": 21, "3PT%": .381, "FTM": 6, "FTA": 8, "FT%": .75, "+/-": 11},
            {"sbc_team": "Baltimore", "display_player": "Player Two", "GP": 3, "MP": 88, "PTS": 65, "OREB": 4, "DREB": 14, "AST": 10, "ST": 3, "BLK": 1, "TO": 6, "TS%": .58, "2PTM": 18, "2PTA": 34, "2PT%": .529, "3PTM": 7, "3PTA": 22, "3PT%": .318, "FTM": 6, "FTA": 8, "FT%": .75, "+/-": -11},
        ])

        trend = pd.DataFrame({
            "game_date": ["20260401", "20260402"],
            "Vegas": [190, 253.5],
            "Baltimore": [205, 159.5],
        })
        result = build_matchup_recap_image(
            matchup,
            pd.DataFrame(category_rows),
            players,
            trend,
            matchup_date_label="Apr 1-Apr 7",
        )
        rendered = Image.open(BytesIO(result))

        self.assertEqual(rendered.format, "PNG")
        self.assertEqual(rendered.size, (2000, 2300))

        mobile_result = build_mobile_matchup_recap_image(
            matchup,
            pd.DataFrame(category_rows),
            players,
            trend,
            matchup_date_label="Apr 1-Apr 7",
        )
        mobile_rendered = Image.open(BytesIO(mobile_result))
        self.assertEqual(mobile_rendered.format, "PNG")
        self.assertEqual(mobile_rendered.size, (1080, 2800))

    @patch("functions._scoreboard_logo_bytes", return_value=None)
    def test_builds_projected_standings_bracket(self, _mock_logo):
        west = pd.DataFrame([
            {"Team": "Vegas", "FullTeam": "Vegas Blackjack", "wins": 20, "losses": 10, "GB": "-", "Streak": "W3", "Last10": "7-3"},
        ])
        east = pd.DataFrame([
            {"Team": "Baltimore", "FullTeam": "Baltimore Blue Crabs", "wins": 19, "losses": 11, "GB": "1", "Streak": "L1", "Last10": "6-4"},
        ])

        result = build_standings_bracket_image(west, east, pd.DataFrame(), "2025-26", "Mar 23-Mar 29")
        rendered = Image.open(BytesIO(result))

        self.assertEqual(rendered.format, "PNG")
        self.assertEqual(rendered.size, (3800, 2000))

        mobile_result = build_mobile_standings_image(west, east, pd.DataFrame(), "2025-26", "Mar 23-Mar 29")
        mobile_rendered = Image.open(BytesIO(mobile_result))
        self.assertEqual(mobile_rendered.format, "PNG")
        self.assertEqual(mobile_rendered.size, (1080, 3690))

    @patch("functions._scoreboard_logo_bytes", return_value=None)
    def test_builds_weekly_matchup_preview(self, _mock_logo):
        matchups = pd.DataFrame([
            {"Game_ID": "1", "TeamA": "Vegas", "TeamB": "Baltimore", "TeamA_record": "8-2", "TeamB_record": "7-3", "Type": "Regular Season"},
            {"Game_ID": "2", "TeamA": "Anaheim", "TeamB": "Pittsburgh", "TeamA_record": "6-4", "TeamB_record": "6-4", "Type": "Regular Season"},
        ])
        featured = [matchups.iloc[0].to_dict(), matchups.iloc[1].to_dict()]

        result = build_matchup_preview_image(matchups, featured, [{}, {}], "2025-26", "Jan 5-Jan 11")
        rendered = Image.open(BytesIO(result))

        self.assertEqual(rendered.format, "PNG")
        self.assertEqual(rendered.size, (3000, 2000))

        mobile_result = build_mobile_matchup_preview_image(matchups, featured, [{}, {}], "2025-26", "Jan 5-Jan 11")
        mobile_rendered = Image.open(BytesIO(mobile_result))
        self.assertEqual(mobile_rendered.format, "PNG")
        self.assertEqual(mobile_rendered.size, (1080, 166 + 52 + 2 * 56 + 24 + 2 * 1080 + 20 + 48))

    @patch("functions._scoreboard_logo_bytes", return_value=None)
    def test_builds_record_leader_announcement(self, _mock_logo):
        result = build_record_leader_announcement_image(
            "Anaheim", "GP", "Jarrett Allen", "Rudy Gobert", 322, 321
        )
        rendered = Image.open(BytesIO(result))

        self.assertEqual(rendered.format, "PNG")
        self.assertEqual(rendered.size, (1080, 1350))


if __name__ == "__main__":
    unittest.main()
