import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gelecek_dalga_kehaneti import GelecekDalgaKehaneti


class GelecekDalgaKehanetiTests(unittest.TestCase):
    def test_forecast_is_labeled_as_simulation_without_confidence_claim(self):
        forecast = GelecekDalgaKehaneti(rng=Random(0)).viral_dalga_tahmin_et()

        self.assertEqual(forecast["veri_kaynagi"], "simülasyon")
        self.assertIsNone(forecast["tahmin_guven_skoru"])
        self.assertIn("doğrulanmış tahmin", forecast["tahmin_notu"])
        self.assertIn("trend_adi", forecast)

    def test_analysis_horizon_is_preserved(self):
        forecast = GelecekDalgaKehaneti(analiz_ufku="Gelecek 30 Gün", rng=Random(0)).viral_dalga_tahmin_et()

        self.assertEqual(forecast["analiz_ufku"], "Gelecek 30 Gün")

    def test_forecast_can_be_queued_for_review(self):
        forecaster = GelecekDalgaKehaneti(rng=Random(0))
        forecast = forecaster.viral_dalga_tahmin_et()
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            task = forecaster.inceleme_kuyruguna_ekle(forecast, db_path=db_path)
            connection = sqlite3.connect(db_path)
            try:
                row = connection.execute(
                    "SELECT account_id, post_id, status FROM task_queue"
                ).fetchone()
            finally:
                connection.close()

        self.assertEqual(row, ("gelecek_dalga_kehaneti", task["post_id"], "pending"))
        self.assertEqual(task["payload"]["status"], "pending_review")

    def test_invalid_horizon_and_empty_scenarios_are_rejected(self):
        with self.assertRaises(ValueError):
            GelecekDalgaKehaneti(analiz_ufku=" ")
        with self.assertRaises(ValueError):
            GelecekDalgaKehaneti(senaryolar=[]).viral_dalga_tahmin_et()


if __name__ == "__main__":
    unittest.main()