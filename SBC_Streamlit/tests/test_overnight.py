from __future__ import annotations

import contextlib
import io
import json
import os
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from sbc_backend.jobs.overnight import _discord_webhook_urls, main, publish_fantrax_rotation
from sbc_backend.fantrax_rotation import RotationPeriod, planned_post_kinds, simulated_today


class OvernightTests(unittest.TestCase):
    def test_multiple_discord_webhooks_support_newlines_commas_and_legacy_secret(self):
        with patch.dict(
            os.environ,
            {
                "DISCORD_WEBHOOK_URLS": "https://discord.test/one\nhttps://discord.test/two, https://discord.test/one",
                "DISCORD_WEBHOOK_URL": "https://discord.test/legacy",
                "DISCORD_WEBHOOK_URL_MOBILE": "",
                "DISCORD_WEBHOOK_URL_WEB": "",
                "SBC_DISCORD_ROUTING_MODE": "split",
            },
            clear=False,
        ):
            self.assertEqual(
                _discord_webhook_urls(),
                [
                    "https://discord.test/one",
                    "https://discord.test/two",
                    "https://discord.test/legacy",
                ],
            )

    def test_rotation_routes_web_mobile_and_record_posts(self):
        period = RotationPeriod(2026, 34, date(2026, 2, 19), date(2026, 2, 20), date(2026, 2, 20))
        rotation = SimpleNamespace(
            period=period,
            build_posts=lambda kinds: ([
                SimpleNamespace(kind="overnight_scores", filename="web.png", image_bytes=b"web"),
                SimpleNamespace(kind="mobile_overnight_scores", filename="mobile.png", image_bytes=b"mobile"),
                SimpleNamespace(kind="record_leader", filename="record.png", image_bytes=b"record"),
            ], []),
        )
        context = SimpleNamespace(repository=object(), target_date=date(2026, 8, 7), fantrax_slot="overnight")
        with (
            patch.dict(
                os.environ,
                {
                    "DISCORD_WEBHOOK_URL_MOBILE": "https://discord.test/mobile",
                    "DISCORD_WEBHOOK_URL_WEB": "https://discord.test/web",
                    "DISCORD_WEBHOOK_URLS": "",
                    "DISCORD_WEBHOOK_URL": "",
                    "SBC_DISCORD_ROUTING_MODE": "split",
                },
                clear=False,
            ),
            patch("sbc_backend.jobs.overnight.FantraxRotation", return_value=rotation),
            patch("sbc_backend.jobs.overnight.fantrax.post_fantrax_webhook") as post,
            patch("sbc_backend.jobs.overnight.time.sleep"),
        ):
            result = publish_fantrax_rotation(context)

        self.assertEqual(post.call_count, 4)
        self.assertEqual(
            [call.args[0] for call in post.call_args_list],
            [
                "https://discord.test/web",
                "https://discord.test/mobile",
                "https://discord.test/web",
                "https://discord.test/mobile",
            ],
        )
        self.assertEqual(result["destinations"], 2)
        self.assertEqual([item["destinations"] for item in result["published"]], [1, 1, 2])
        self.assertEqual([item["delivered"] for item in result["published"]], [1, 1, 2])

    def test_primary_mode_sends_every_render_to_original_private_webhook(self):
        period = RotationPeriod(2026, 34, date(2026, 2, 19), date(2026, 2, 20), date(2026, 2, 20))
        rotation = SimpleNamespace(
            period=period,
            build_posts=lambda kinds: ([
                SimpleNamespace(kind="overnight_scores", filename="web.png", image_bytes=b"web"),
                SimpleNamespace(kind="mobile_overnight_scores", filename="mobile.png", image_bytes=b"mobile"),
                SimpleNamespace(kind="record_leader", filename="record.png", image_bytes=b"record"),
            ], []),
        )
        context = SimpleNamespace(repository=object(), target_date=date(2026, 8, 7), fantrax_slot="overnight")
        with (
            patch.dict(
                os.environ,
                {
                    "SBC_DISCORD_ROUTING_MODE": "primary",
                    "DISCORD_WEBHOOK_URL": "https://discord.test/private",
                    "DISCORD_WEBHOOK_URLS": "",
                    "DISCORD_WEBHOOK_URL_MOBILE": "https://discord.test/mobile",
                    "DISCORD_WEBHOOK_URL_WEB": "https://discord.test/web",
                },
                clear=False,
            ),
            patch("sbc_backend.jobs.overnight.FantraxRotation", return_value=rotation),
            patch("sbc_backend.jobs.overnight.fantrax.post_fantrax_webhook") as post,
            patch("sbc_backend.jobs.overnight.time.sleep"),
        ):
            result = publish_fantrax_rotation(context)

        self.assertEqual(post.call_count, 3)
        self.assertEqual([call.args[0] for call in post.call_args_list], ["https://discord.test/private"] * 3)
        self.assertEqual(result["destinations"], 1)
        self.assertEqual([item["destinations"] for item in result["published"]], [1, 1, 1])

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
