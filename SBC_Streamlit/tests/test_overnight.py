from __future__ import annotations

import contextlib
import io
import json
import unittest

from sbc_backend.jobs.overnight import main


class OvernightTests(unittest.TestCase):
    def test_dry_run_resolves_without_network(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["--dry-run", "--date", "2026-07-30", "--jobs", "validate"])
        self.assertEqual(status, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["nba_season"], "2026-27")
        self.assertEqual(payload["jobs"], ["validate"])


if __name__ == "__main__":
    unittest.main()
