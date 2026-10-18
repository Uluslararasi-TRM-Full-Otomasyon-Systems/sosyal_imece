import unittest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ilk_uc_saniye_motoru import _HOOK_TEMPLATES, kanca_ekle
from muzakere_ajani import tedarikci_analiz_et


class AdvancedSmartModuleTests(unittest.TestCase):
    def test_hook_uses_product_and_target_audience(self):
        with patch("ilk_uc_saniye_motoru.random.choice", return_value=_HOOK_TEMPLATES[1]):
            hook = kanca_ekle("Akıllı lamba", "Ev kullanıcıları")

        self.assertIn("Akıllı lamba", hook)
        self.assertIn("Ev kullanıcıları", hook)

    def test_hook_rejects_empty_product(self):
        with self.assertRaises(ValueError):
            kanca_ekle("  ")

    def test_supplier_report_discloses_missing_profile_data(self):
        report = tedarikci_analiz_et("Tedarik A.Ş.", "Ayşe Hanım")

        self.assertEqual(report["firma_adi"], "Tedarik A.Ş.")
        self.assertEqual(report["yetkili_adi"], "Ayşe Hanım")
        self.assertIn("verisi yok", report["profil_tipi"])
        self.assertIn("Ayşe Hanım", report["ilk_cumle_taslagi"])

    def test_supplier_report_rejects_empty_names(self):
        with self.assertRaises(ValueError):
            tedarikci_analiz_et("", "Ayşe Hanım")


if __name__ == "__main__":
    unittest.main()