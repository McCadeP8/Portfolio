from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from matplotlib import font_manager

from jersey_engine import (
    JerseyConfig,
    _front_wordmark_text,
    _show_front_league_mark,
    _uniform_stripe_style,
    apply_resolved_brand_font,
    resolve_brand_font_path,
)


class JerseyFontTests(unittest.TestCase):
    def tearDown(self):
        resolve_brand_font_path.cache_clear()

    def test_missing_saved_font_uses_matching_cached_brand_font(self):
        with tempfile.TemporaryDirectory() as temporary:
            cache_root = Path(temporary)
            cached_font = cache_root / "bungee.ttf"
            shutil.copyfile(font_manager.findfont("DejaVu Sans"), cached_font)
            config = JerseyConfig(font_family="Bungee", font_path="C:/missing/bungee.ttf")

            resolved = apply_resolved_brand_font(config, cache_root)

            self.assertEqual(Path(resolved.font_path), cached_font)

    def test_statement_jerseys_never_show_fallback_sbc_marks(self):
        config = JerseyConfig(edition="Statement", wordmark="SBC", show_league_mark=True)

        self.assertEqual(_front_wordmark_text(config), "")
        self.assertFalse(_show_front_league_mark(config))

    def test_standard_jerseys_keep_configured_sbc_marks(self):
        config = JerseyConfig(edition="Association", wordmark="SBC", show_league_mark=True)

        self.assertEqual(_front_wordmark_text(config), "SBC")
        self.assertTrue(_show_front_league_mark(config))

    def test_statement_jerseys_never_inherit_default_stripes(self):
        config = JerseyConfig(
            edition="Statement",
            stripe_style="Side panels",
            shorts_stripe_style="Double side",
        )

        self.assertEqual(_uniform_stripe_style(config), "None")
        self.assertEqual(_uniform_stripe_style(config, shorts=True), "None")

    def test_standard_jerseys_keep_their_configured_stripes(self):
        config = JerseyConfig(
            edition="Icon",
            stripe_style="Side panels",
            shorts_stripe_style="Double side",
        )

        self.assertEqual(_uniform_stripe_style(config), "Side panels")
        self.assertEqual(_uniform_stripe_style(config, shorts=True), "Double side")


if __name__ == "__main__":
    unittest.main()
