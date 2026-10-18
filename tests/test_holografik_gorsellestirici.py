import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from holografik_gorsellestirici import HolografikGorsellestirici


class HolografikGorsellestiriciTests(unittest.TestCase):
    def test_generates_svg_concept_preview_not_fake_video(self):
        package = HolografikGorsellestirici("Solar kahve makinesi").gorsel_ve_mockup_uret()

        self.assertIn("<svg", package["preview_svg"])
        self.assertIn("Solar kahve makinesi", package["preview_svg"])
        self.assertFalse(package["gercek_render_uretildi"])
        self.assertIn("360° video üretilmedi", package["durum"])
        self.assertTrue(package["render_prompt_taslagi"])

    def test_escapes_user_concept_in_svg(self):
        package = HolografikGorsellestirici("A&B <konsept>").gorsel_ve_mockup_uret()

        self.assertIn("A&amp;B &lt;konsept&gt;", package["preview_svg"])
        self.assertNotIn("A&B <konsept>", package["preview_svg"])

    def test_empty_concept_is_rejected(self):
        with self.assertRaises(ValueError):
            HolografikGorsellestirici(" ")


if __name__ == "__main__":
    unittest.main()