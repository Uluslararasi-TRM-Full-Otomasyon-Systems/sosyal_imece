import sys
import unittest
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nor_davranis_gozcusu import NorDavranisGozcusu


class NorDavranisGozcusuTests(unittest.TestCase):
    def test_default_result_is_aggregate_and_simulated(self):
        report = NorDavranisGozcusu(rng=Random(0)).kitle_ruh_hali_analiz_et()

        self.assertEqual(report["veri_kaynagi"], "simülasyon")
        self.assertEqual(report["bireysel_profil_cikarimi"], "Yapılmaz")
        self.assertIn("tamamlama_orani", report["gozlemlenen_icerik_sinyali"])
        self.assertNotIn("guvenilirlik_orani", report)
        self.assertNotIn("ruh_hali", report)

    def test_platform_is_preserved(self):
        report = NorDavranisGozcusu(platform="YouTube Shorts", rng=Random(0)).kitle_ruh_hali_analiz_et()

        self.assertEqual(report["platform"], "YouTube Shorts")

    def test_empty_platform_and_signal_list_are_rejected(self):
        with self.assertRaises(ValueError):
            NorDavranisGozcusu(platform=" ")
        with self.assertRaises(ValueError):
            NorDavranisGozcusu(sinyaller=[]).kitle_ruh_hali_analiz_et()

    def test_out_of_range_aggregate_signal_is_rejected(self):
        signals = [{
            "icerik_turu": "invalid",
            "tamamlama_orani": 101,
            "kaydetme_orani": 1,
            "paylasim_orani": 1,
        }]
        with self.assertRaises(ValueError):
            NorDavranisGozcusu(sinyaller=signals).kitle_ruh_hali_analiz_et()


if __name__ == "__main__":
    unittest.main()