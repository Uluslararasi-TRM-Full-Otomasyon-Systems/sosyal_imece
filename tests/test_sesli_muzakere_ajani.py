import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sesli_muzakere_ajani import SesliMuzakereAjani


class SesliMuzakereAjaniTests(unittest.TestCase):
    def test_report_contains_script_and_discloses_no_voice_clone(self):
        report = SesliMuzakereAjani(
            "Global Tedarik A.Ş.", "Mehmet Bey", hedef_iskonto=12.5
        ).muzakere_taslagi_olustur()

        self.assertEqual(report["firma"], "Global Tedarik A.Ş.")
        self.assertIn("Mehmet Bey", report["ornek_sesli_cumle"])
        self.assertIn("klonlama kapalı", report["ses_sentez_durumu"])
        self.assertIn("%12.5", report["hedef_iskonto_notu"])

    def test_report_does_not_infer_contact_psychology(self):
        report = SesliMuzakereAjani(
            "Tedarik A.Ş.", "Ayşe Hanım"
        ).muzakere_taslagi_olustur()

        self.assertIn("kişiye göre çıkarım yapılmaz", report["ses_tonu_kriteri"])
        self.assertIsNone(report["hedef_iskonto_yuzdesi"])

    def test_invalid_discount_is_rejected(self):
        with self.assertRaises(ValueError):
            SesliMuzakereAjani("Firma", "Yetkili", hedef_iskonto=120)

    def test_empty_contact_is_rejected(self):
        with self.assertRaises(ValueError):
            SesliMuzakereAjani("Firma", " ")


if __name__ == "__main__":
    unittest.main()