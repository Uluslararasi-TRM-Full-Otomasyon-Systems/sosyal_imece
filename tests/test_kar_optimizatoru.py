import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kar_optimizatoru import KarOptimizatoru


class KarOptimizatoruTests(unittest.TestCase):
    def test_calculates_conversion_profit_and_target_price(self):
        report = KarOptimizatoru().karlilik_ve_donusum_analizi(
            urun="Örnek ürün",
            satis_fiyati=100,
            birim_maliyet=40,
            ziyaret_sayisi=100,
            siparis_sayisi=10,
            reklam_gideri=100,
            hedef_marj=50,
        )

        self.assertEqual(report["ciro"], 1000)
        self.assertEqual(report["brut_kar"], 600)
        self.assertEqual(report["net_kar"], 500)
        self.assertEqual(report["donusum_orani"], 10)
        self.assertEqual(report["reklam_dahil_net_marj"], 50)
        self.assertEqual(report["hedef_fiyat_onerisi"], 100)
        self.assertIn("otomatik olarak değiştirilmez", report["fiyat_onerisi_varsayimi"])

    def test_no_orders_produces_no_price_recommendation(self):
        report = KarOptimizatoru().karlilik_ve_donusum_analizi(
            "Örnek", 100, 40, 0, 0
        )

        self.assertIsNone(report["donusum_orani"])
        self.assertIsNone(report["hedef_fiyat_onerisi"])

    def test_invalid_data_is_rejected(self):
        with self.assertRaises(ValueError):
            KarOptimizatoru().karlilik_ve_donusum_analizi("Ürün", 100, 20, 1, 2)
        with self.assertRaises(ValueError):
            KarOptimizatoru().karlilik_ve_donusum_analizi("Ürün", 100, 20, 10, 1, hedef_marj=100)
        with self.assertRaises(ValueError):
            KarOptimizatoru().karlilik_ve_donusum_analizi("Ürün", float("nan"), 20, 10, 1)

    def test_empty_store_or_product_is_rejected(self):
        with self.assertRaises(ValueError):
            KarOptimizatoru(" ")
        with self.assertRaises(ValueError):
            KarOptimizatoru().karlilik_ve_donusum_analizi(" ", 100, 20, 10, 1)


if __name__ == "__main__":
    unittest.main()