from __future__ import annotations

import contextlib
import io
import unittest
from unittest.mock import patch

import big_data


class RefreshNotificationTests(unittest.TestCase):
    def test_routine_progress_is_logged_without_sending_discord(self):
        output = io.StringIO()
        with (
            patch.object(big_data, "DISCORD_WEBHOOK_URL", "https://discord.test/webhook"),
            patch.object(big_data, "send_discord_message") as send,
            contextlib.redirect_stdout(output),
        ):
            big_data.notify("Refreshed snapshot: cap sheet")

        self.assertIn("Refreshed snapshot: cap sheet", output.getvalue())
        send.assert_not_called()

    def test_actionable_problem_sends_discord(self):
        message = "Skipped snapshot refresh for cap sheet: TimeoutError"
        with (
            patch.object(big_data, "DISCORD_WEBHOOK_URL", "https://discord.test/webhook"),
            patch.object(big_data, "send_discord_message") as send,
        ):
            big_data.notify(message, alert=True)

        send.assert_called_once_with("https://discord.test/webhook", message)


if __name__ == "__main__":
    unittest.main()
