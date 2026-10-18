import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from geo_spatial_niche_profiler import GeoSpatialNicheProfiler


class GeoSpatialNicheProfilerTests(unittest.TestCase):
    def test_default_result_is_simulated_and_does_not_claim_live_geo_data(self):
        report = GeoSpatialNicheProfiler(rng=Random(0)).bolgesel_niche_tara()

        self.assertEqual(report["veri_kaynagi"], "simülasyon")
        self.assertFalse(report["canli_hava_ve_koordinat_verisi"])
        self.assertIn("değiştirilmedi", report["aksiyon_durumu"])
        self.assertIn("tespit_edilen_niche", report)

    def test_region_hint_selects_matching_demo_opportunity(self):
        report = GeoSpatialNicheProfiler(
            hedef_bolge="Kuşadası / Akdeniz Havzası", rng=Random(1)
        ).bolgesel_niche_tara()

        self.assertIn("Kuşadası", report["bolge"])

    def test_queues_review_task_as_pending(self):
        profiler = GeoSpatialNicheProfiler(rng=Random(0))
        report = profiler.bolgesel_niche_tara()
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            task = profiler.inceleme_kuyruguna_ekle(report, db_path=db_path)
            connection = sqlite3.connect(db_path)
            try:
                row = connection.execute(
                    "SELECT account_id, post_id, status FROM task_queue"
                ).fetchone()
            finally:
                connection.close()

        self.assertEqual(row, ("geo_spatial_niche_profiler", task["post_id"], "pending"))
        self.assertEqual(task["payload"]["status"], "pending_review")

    def test_invalid_region_and_report_are_rejected(self):
        with self.assertRaises(ValueError):
            GeoSpatialNicheProfiler(hedef_bolge=" ")
        with self.assertRaises(ValueError):
            GeoSpatialNicheProfiler().inceleme_kuyruguna_ekle({})


if __name__ == "__main__":
    unittest.main()