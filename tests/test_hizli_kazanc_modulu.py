import ast
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hizli_kazanc_modulu import HizliKazancModulu
from gorev_incele_ve_onayla import autonomous_approve_and_transfer
from trm_master_kernel import MasterOrchestrator


class HizliKazancTests(unittest.TestCase):
    def test_simulation_creates_tagged_queue_tasks_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "affiliate.db"
            gateway = Mock()
            gateway.akilli_yonlendir.return_value = {"durum": "draft_ready"}

            result = HizliKazancModulu(
                queue_db=db_path,
                mode="simulate",
                gateway=gateway,
            ).kampanya_uret_ve_kuyruga_ekle()

            with closing(sqlite3.connect(db_path)) as connection:
                rows = connection.execute(
                    "SELECT account_id, post_id, payload, status FROM task_queue ORDER BY id"
                ).fetchall()

        self.assertEqual(result["durum"], "completed")
        self.assertEqual(result["kuyruga_eklenen"], len(HizliKazancModulu.SIMULATED_TRENDS))
        self.assertTrue(all(row[0] == "trm_hizli_kazanc" and row[3] == "pending" for row in rows))
        for row in rows:
            payload = ast.literal_eval(row[2])["payload"]
            self.assertEqual(payload["task_type"], "gelir_getiren_gorev")
            self.assertEqual(payload["status"], "pending_review")
            self.assertEqual(payload["affiliate_link_status"], "fallback_redirect")
            self.assertFalse(payload["commission_eligible"])
            self.assertTrue(payload["affiliate_link_draft"].startswith("https://trendurunlermarket.com/urun/"))
            self.assertFalse(payload["auto_publish"])
            self.assertTrue(payload["social_media_hooks"])
        self.assertEqual(gateway.akilli_yonlendir.call_count, len(rows))

    def test_live_mode_uses_scraper_and_uses_configured_affiliate_tag(self):
        scraper = Mock()
        scraper.fetch_trends.return_value = [{
            "title": "Deneme urunu",
            "description": "Aciklama",
            "source": "test",
            "url": "https://shop.example/product/1",
        }]
        scraper.errors = []
        gateway = Mock()
        gateway.akilli_yonlendir.return_value = {"durum": "draft_ready"}

        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "affiliate.db"
            result = HizliKazancModulu(
                queue_db=db_path,
                mode="live",
                scraper=scraper,
                affiliate_tag="trm-01",
                gateway=gateway,
            ).kampanya_uret_ve_kuyruga_ekle()

        scraper.fetch_trends.assert_called_once_with()
        self.assertEqual(result["gorevler"][0]["payload"]["affiliate_link_draft"],
                         "https://shop.example/product/1?tag=trm-01")

    def test_repeated_campaign_is_not_added_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "affiliate.db"
            first = HizliKazancModulu(queue_db=db_path, mode="simulate")
            second = HizliKazancModulu(queue_db=db_path, mode="simulate")

            first_result = first.kampanya_uret_ve_kuyruga_ekle()
            second_result = second.kampanya_uret_ve_kuyruga_ekle()

        self.assertEqual(first_result["kuyruga_eklenen"], 3)
        self.assertEqual(second_result["kuyruga_eklenen"], 0)
        self.assertEqual(second_result["atlanan_yinelenen"], 3)

    def test_autonomous_flow_approves_and_simulates_bridge_transfer(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "affiliate.db"
            gateway = Mock()
            gateway.akilli_yonlendir.return_value = {"durum": "draft_ready"}
            HizliKazancModulu(
                queue_db=db_path,
                mode="simulate",
                gateway=gateway,
            ).kampanya_uret_ve_kuyruga_ekle()

            report = autonomous_approve_and_transfer(db_path)

            with closing(sqlite3.connect(db_path)) as connection:
                rows = connection.execute(
                    "SELECT status, payload FROM task_queue ORDER BY id"
                ).fetchall()

        self.assertEqual(report["durum"], "completed")
        self.assertEqual(report["onaylanan"], 3)
        self.assertEqual(len(report["magaza_koprusu"]["kayitlar"]), 3)
        self.assertTrue(all(row[0] == "approved" for row in rows))
        for _status, raw_payload in rows:
            payload = ast.literal_eval(raw_payload)["payload"]
            self.assertEqual(payload["status"], "approved")
            self.assertEqual(payload["approval_status"], "approved")

    def test_master_kernel_can_run_the_autonomous_campaign_cycle(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "affiliate.db"
            health_db = Path(directory) / "health.db"
            with patch.dict("os.environ", {"TRM_AUTONOMOUS_DISTRIBUTION_ENABLED": "true"}), patch(
                "oto_onarim_ajani.socket.create_connection"
            ), patch(
                "oto_onarim_ajani.urlopen", side_effect=OSError
            ):
                report = MasterOrchestrator().tam_sistem_dongusunu_baslat({
                    "hizli_kazanc": {"mode": "simulate"},
                    "affiliate_queue_db": db_path,
                    "queue_db": health_db,
                    "health_url": "http://127.0.0.1:1/health",
                })

            with closing(sqlite3.connect(db_path)) as connection:
                statuses = connection.execute(
                    "SELECT status FROM task_queue ORDER BY id"
                ).fetchall()
                distributions = connection.execute(
                    "SELECT COUNT(*) FROM distribution_outbox"
                ).fetchone()[0]

        steps = {step["modul"]: step for step in report["adimlar"]}
        self.assertEqual(steps["Hızlı Kazanç Affiliate Kampanya Taslakları"]["durum"], "simulated")
        self.assertEqual(steps["Otonom Kampanya Doğrulama ve Köprü Aktarımı"]["detay"]["onaylanan"], 3)
        self.assertTrue(all(row[0] == "approved" for row in statuses))
        self.assertEqual(distributions, 9)


if __name__ == "__main__":
    unittest.main()