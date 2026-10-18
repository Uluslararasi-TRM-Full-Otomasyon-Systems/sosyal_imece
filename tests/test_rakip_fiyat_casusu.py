import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rakip_fiyat_casusu import RakipFiyatCasusu


class RakipFiyatCasusuTests(unittest.TestCase):
    def test_computes_market_average_median_and_relative_gap(self):
        report = RakipFiyatCasusu().pazar_fiyat_gözlemi_yap(
            "Vantilatör", 620, [600, 650, 700]
        )

        self.assertEqual(report["pazar_ortalama_fiyat"], 650)
        self.assertEqual(report["pazar_medyan_fiyat"], 650)
        self.assertAlmostEqual(report["ortalama_fiyata_gore_fark_yuzde"], -4.615384615)
        self.assertFalse(report["otomatik_fiyat_degisikligi"])
        self.assertEqual(report["veri_kaynagi"], "kullanıcı tarafından girilen fiyat gözlemleri")

    def test_above_market_advice_does_not_force_discount(self):
        report = RakipFiyatCasusu().pazar_fiyat_gözlemi_yap(
            "Şarj standı", 950, [890, 900]
        )

        self.assertIn("ürün farkı ve marjı inceleyin", report["tavsiye_edilen_aksiyon"])

    def test_rejects_empty_product_or_invalid_prices(self):
        with self.assertRaises(ValueError):
            RakipFiyatCasusu().pazar_fiyat_gözlemi_yap(" ", 100, [90])
        with self.assertRaises(ValueError):
            RakipFiyatCasusu().pazar_fiyat_gözlemi_yap("Ürün", 100, [])
        with self.assertRaises(ValueError):
            RakipFiyatCasusu().pazar_fiyat_gözlemi_yap("Ürün", 100, [float("nan")])

    def test_rejects_invalid_category(self):
        with self.assertRaises(ValueError):
            RakipFiyatCasusu(hedef_kategori=" ")


if __name__ == "__main__":
    unittest.main()