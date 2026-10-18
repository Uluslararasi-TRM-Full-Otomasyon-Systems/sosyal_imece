import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from oz_evrilen_kod_ajani import OzEvrilenKodAjani


class OzEvrilenKodAjaniTests(unittest.TestCase):
    def test_scans_allowlisted_sources_without_mutation_claims(self):
        report = OzEvrilenKodAjani().kod_ve_prompt_optimizasyonu_tara()

        self.assertEqual(len(report["bilesenler"]), 2)
        self.assertTrue(all(item["durum"] == "analyzed" for item in report["bilesenler"]))
        self.assertIsNone(report["guven_orani"])
        self.assertFalse(report["otomatik_kod_degisikligi"])
        self.assertFalse(report["otomatik_prompt_degisikligi"])

    def test_can_scan_one_component(self):
        component = "DispatchQueueManager (SQLite)"
        report = OzEvrilenKodAjani().kod_ve_prompt_optimizasyonu_tara(component)

        self.assertEqual(len(report["bilesenler"]), 1)
        self.assertTrue(any("pending durum filtresi bulundu" in item for item in report["bilesenler"][0]["bulgular"]))

    def test_review_report_can_be_queued(self):
        agent = OzEvrilenKodAjani()
        report = agent.kod_ve_prompt_optimizasyonu_tara()
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            task = agent.inceleme_kuyruguna_ekle(report, db_path=db_path)
            connection = sqlite3.connect(db_path)
            try:
                row = connection.execute(
                    "SELECT account_id, post_id, status FROM task_queue"
                ).fetchone()
            finally:
                connection.close()

        self.assertEqual(row, ("oz_evrilen_kod_ajani", task["post_id"], "pending"))
        self.assertEqual(task["payload"]["status"], "pending_review")

    def test_unknown_component_and_invalid_report_are_rejected(self):
        agent = OzEvrilenKodAjani()
        with self.assertRaises(ValueError):
            agent.kod_ve_prompt_optimizasyonu_tara("unknown")
        with self.assertRaises(ValueError):
            agent.inceleme_kuyruguna_ekle({})

    def test_bom_prefixed_source_is_parsed(self):
        root = Path(__file__).resolve().parents[1]
        report = OzEvrilenKodAjani(project_root=root).kod_ve_prompt_optimizasyonu_tara(
            "DispatchQueueManager (SQLite)"
        )

        self.assertEqual(report["bilesenler"][0]["durum"], "analyzed")


if __name__ == "__main__":
    unittest.main()