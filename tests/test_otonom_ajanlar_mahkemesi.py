import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from otonom_ajanlar_mahkemesi import OtonomAjanlarMahkemesi


class OtonomAjanlarMahkemesiTests(unittest.TestCase):
    def test_missing_evidence_defers_review(self):
        report = OtonomAjanlarMahkemesi().ajanlar_arasi_munazara_ve_karar(
            savunma="Lansman yapılması öneriliyor."
        )

        self.assertEqual(report["durum"], "insufficient_information")
        self.assertFalse(report["otomatik_onay"])
        self.assertIsNone(report["guven_puani"])

    def test_objections_or_risks_require_human_review(self):
        report = OtonomAjanlarMahkemesi().ajanlar_arasi_munazara_ve_karar(
            savunma="Ürün uygun görünüyor.",
            kanitlar=["Maliyet tablosu"],
            itirazlar=["Kargo maliyeti doğrulanmadı"],
            riskler=["Marj hassasiyeti"],
        )

        self.assertEqual(report["durum"], "review_required")
        self.assertIn("ertelendi", report["nihai_karar"])

    def test_complete_inputs_are_only_ready_for_human_decision(self):
        report = OtonomAjanlarMahkemesi().ajanlar_arasi_munazara_ve_karar(
            savunma="Ürün taslağı hazır.",
            kanitlar=["Maliyet tablosu", "Tedarikçi teknik föyü"],
        )

        self.assertEqual(report["durum"], "human_review_ready")
        self.assertIn("otomatik onay verilmedi", report["nihai_karar"])

    def test_report_is_added_only_to_pending_review_queue(self):
        court = OtonomAjanlarMahkemesi("Test kararı")
        report = court.ajanlar_arasi_munazara_ve_karar(
            savunma="Savunma", kanitlar=["Kanıt"]
        )
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            task = court.inceleme_kuyruguna_ekle(report, db_path=db_path)
            connection = sqlite3.connect(db_path)
            try:
                row = connection.execute(
                    "SELECT account_id, post_id, status FROM task_queue"
                ).fetchone()
            finally:
                connection.close()

        self.assertEqual(row, ("otonom_ajanlar_mahkemesi", task["post_id"], "pending"))
        self.assertEqual(task["payload"]["status"], "pending_review")

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(ValueError):
            OtonomAjanlarMahkemesi(" ")
        with self.assertRaises(ValueError):
            OtonomAjanlarMahkemesi().ajanlar_arasi_munazara_ve_karar(savunma=123)


if __name__ == "__main__":
    unittest.main()