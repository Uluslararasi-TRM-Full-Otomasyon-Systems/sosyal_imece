import sqlite3
import sys
import tempfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from trm_master_kernel import MasterOrchestrator


class MasterKernelTests(unittest.TestCase):
    def test_runs_fifteen_steps_and_reports_missing_inputs(self):
        kernel = MasterOrchestrator()
        with patch("oto_onarim_ajani.socket.create_connection"), patch(
            "oto_onarim_ajani.urlopen", side_effect=OSError
        ):
            report = kernel.tam_sistem_dongusunu_baslat({
                "health_url": "http://127.0.0.1:1/health",
                "queue_db": Path(tempfile.gettempdir()) / "missing-master-kernel-db.sqlite",
            })

        self.assertEqual(report["modul_sayisi"], 15)
        self.assertEqual(len(report["adimlar"]), 15)
        self.assertIn("Rakip Fiyat Karşılaştırması", report["girdi_bekleyen_moduller"])
        self.assertFalse(report["otomatik_yayin"])
        self.assertFalse(report["otomatik_fiyat_degistirme"])
        self.assertFalse(report["otomatik_kod_degistirme"])

    def test_uses_user_data_for_optional_price_profit_and_supplier_steps(self):
        kernel = MasterOrchestrator()
        with patch("oto_onarim_ajani.socket.create_connection"), patch(
            "oto_onarim_ajani.urlopen", side_effect=OSError
        ):
            report = kernel.tam_sistem_dongusunu_baslat({
                "urun_adi": "Test ürün",
                "fiyat_girdileri": {"bizim_fiyatimiz": 80, "rakip_fiyatlari": [90]},
                "karlilik_girdileri": {
                    "satis_fiyati": 80,
                    "birim_maliyet": 40,
                    "ziyaret_sayisi": 100,
                    "siparis_sayisi": 5,
                },
                "tedarikci_girdileri": {"firma_adi": "Test Ltd", "yetkili_adi": "Yetkili"},
                "health_url": "http://127.0.0.1:1/health",
                "queue_db": Path(tempfile.gettempdir()) / "missing-master-kernel-db.sqlite",
            })

        statuses = {item["modul"]: item["durum"] for item in report["adimlar"]}
        self.assertEqual(statuses["Rakip Fiyat Karşılaştırması"], "completed")
        self.assertEqual(statuses["Kârlılık ve Dönüşüm Analizi"], "completed")
        self.assertEqual(statuses["Müzakere Konuşma Taslağı"], "draft_ready")

    def test_rejects_non_dict_context(self):
        with self.assertRaises(ValueError):
            MasterOrchestrator().tam_sistem_dongusunu_baslat([])

    def test_master_report_can_be_queued_for_human_review(self):
        kernel = MasterOrchestrator()
        with patch("oto_onarim_ajani.socket.create_connection"), patch(
            "oto_onarim_ajani.urlopen", side_effect=OSError
        ):
            report = kernel.tam_sistem_dongusunu_baslat({
                "health_url": "http://127.0.0.1:1/health",
                "queue_db": Path(tempfile.gettempdir()) / "missing-master-kernel-db.sqlite",
            })
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            task = kernel.inceleme_kuyruguna_ekle(report, db_path=db_path)
            connection = sqlite3.connect(db_path)
            try:
                row = connection.execute(
                    "SELECT account_id, post_id, status FROM task_queue"
                ).fetchone()
            finally:
                connection.close()

        self.assertEqual(row, ("trm_master_kernel", task["post_id"], "pending"))
        self.assertEqual(task["payload"]["status"], "pending_review")


if __name__ == "__main__":
    unittest.main()