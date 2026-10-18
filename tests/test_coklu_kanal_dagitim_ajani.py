import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from coklu_kanal_dagitim_ajani import KANALLAR, CokluKanalDagitimAjani


class CokluKanalDagitimAjaniTests(unittest.TestCase):
    def test_prepares_all_channel_drafts_without_claiming_delivery(self):
        agent = CokluKanalDagitimAjani(
            "Akıllı ürün", "Doğrulanmış ürün açıklaması", "https://example.test/item"
        )

        drafts = agent.otonom_yayina_basla()

        self.assertEqual([item["kanal"] for item in drafts], list(KANALLAR))
        self.assertTrue(all("gönderilmedi" in item["durum"] for item in drafts))
        self.assertTrue(all(item["icerik"]["urun_linki"] == "https://example.test/item" for item in drafts))

    def test_prepares_only_selected_channels(self):
        agent = CokluKanalDagitimAjani("Akıllı ürün")

        drafts = agent.otonom_yayina_basla([KANALLAR[0]])

        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0]["kanal"], KANALLAR[0])

    def test_queues_each_draft_for_review(self):
        agent = CokluKanalDagitimAjani("Akıllı ürün")
        drafts = agent.otonom_yayina_basla()
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            tasks = agent.inceleme_kuyruguna_ekle(drafts, db_path=db_path)
            connection = sqlite3.connect(db_path)
            try:
                rows = connection.execute(
                    "SELECT account_id, status FROM task_queue"
                ).fetchall()
            finally:
                connection.close()

        self.assertEqual(len(tasks), len(KANALLAR))
        self.assertEqual(rows, [("multichannel_broadcaster", "pending")] * len(KANALLAR))
        self.assertTrue(all(task["payload"]["status"] == "pending_review" for task in tasks))

    def test_rejects_invalid_input_and_channel(self):
        with self.assertRaises(ValueError):
            CokluKanalDagitimAjani(" ")
        with self.assertRaises(ValueError):
            CokluKanalDagitimAjani("Ürün").otonom_yayina_basla(["Unknown"])
        with self.assertRaises(ValueError):
            CokluKanalDagitimAjani("Ürün").inceleme_kuyruguna_ekle([])


if __name__ == "__main__":
    unittest.main()