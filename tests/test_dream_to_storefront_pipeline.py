import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dream_to_storefront_pipeline import DreamToStorefrontPipeline


class DreamToStorefrontPipelineTests(unittest.TestCase):
    def test_generated_idea_is_marked_as_simulation(self):
        pipeline = DreamToStorefrontPipeline(hedef_pazar="US/EU", rng=Random(0))

        idea = pipeline.pazar_boslugu_ve_fikir_uret()

        self.assertEqual(idea["hedef_pazar"], "US/EU")
        self.assertEqual(idea["veri_kaynagi"], "simülasyon")
        self.assertIn("doğrulaması bekliyor", idea["durum"])

    def test_launch_package_is_a_draft_not_a_store_listing(self):
        pipeline = DreamToStorefrontPipeline(rng=Random(0))
        package = pipeline.lansman_paketi_uret(pipeline.pazar_boslugu_ve_fikir_uret())

        self.assertIn("urun_aciklamasi_taslagi", package)
        self.assertEqual(package["durum"], "Taslak; mağazada yayımlanmadı")
        self.assertEqual(package["veri_kaynagi"], "simülasyon")

    def test_review_task_is_added_to_sqlite_queue(self):
        pipeline = DreamToStorefrontPipeline(rng=Random(0))
        package = pipeline.lansman_paketi_uret(pipeline.pazar_boslugu_ve_fikir_uret())
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            task = pipeline.inceleme_kuyruguna_ekle(package, db_path=db_path)
            connection = sqlite3.connect(db_path)
            try:
                row = connection.execute(
                    "SELECT account_id, post_id, status FROM task_queue"
                ).fetchone()
            finally:
                connection.close()

        self.assertEqual(
            row,
            ("dream_to_storefront_pipeline", task["post_id"], "pending"),
        )
        self.assertEqual(task["payload"]["status"], "pending_review")

    def test_empty_idea_list_and_invalid_package_are_rejected(self):
        with self.assertRaises(ValueError):
            DreamToStorefrontPipeline(fikirler=[]).pazar_boslugu_ve_fikir_uret()
        with self.assertRaises(ValueError):
            DreamToStorefrontPipeline().lansman_paketi_uret({})


if __name__ == "__main__":
    unittest.main()