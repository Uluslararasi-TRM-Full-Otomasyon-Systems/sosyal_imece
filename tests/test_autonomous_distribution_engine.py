import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autonomous_distribution_engine import AutonomousDistributionEngine


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"ok": True}


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse()


class AutonomousDistributionEngineTests(unittest.TestCase):
    def _create_approved_campaign(self, db_path, affiliate_status="fallback_redirect"):
        payload = {
            "task_type": "gelir_getiren_gorev",
            "etiket": "gelir_getiren_gorev",
            "status": "approved",
            "affiliate_link_status": affiliate_status,
            "commission_eligible": affiliate_status == "partner_link",
            "affiliate_link_draft": "https://trendurunlermarket.com/urun/trm-test?ref=test",
            "social_media_hooks": ["Ürün için test kancası"],
            "product": {"title": "Test ürün", "affiliate_url": "https://trendurunlermarket.com/urun/trm-test?ref=test"},
        }
        envelope = {
            "account_id": "trm_hizli_kazanc",
            "post_id": "affiliate-test-1",
            "payload": payload,
        }
        with closing(sqlite3.connect(db_path)) as connection:
            connection.execute(
                "CREATE TABLE task_queue (id INTEGER PRIMARY KEY, account_id TEXT, post_id TEXT, payload TEXT, status TEXT, queued_at TEXT)"
            )
            connection.execute(
                "INSERT INTO task_queue (account_id, post_id, payload, status, queued_at) VALUES (?, ?, ?, ?, ?)",
                (envelope["account_id"], envelope["post_id"], repr(envelope), "approved", "test"),
            )
            connection.commit()

    def test_simulation_queues_hooks_and_link_idempotently(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "distribution.db"
            self._create_approved_campaign(db_path)
            store_result = {"kayitlar": [{"source_key": "affiliate-test-1", "durum": "simulated"}]}
            engine = AutonomousDistributionEngine(db_path=db_path)

            first = engine.distribute_processed(store_result)
            second = engine.distribute_processed(store_result)
            with closing(sqlite3.connect(db_path)) as connection:
                rows = connection.execute(
                    "SELECT channel, status, message, affiliate_url FROM distribution_outbox ORDER BY channel"
                ).fetchall()

        self.assertEqual(first["durum"], "completed")
        self.assertEqual(first["dagitilan"], 3)
        self.assertEqual(second["dagitilan"], 0)
        self.assertEqual(second["yinelenen_atlandi"], 3)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row[1] == "simulated" for row in rows))
        self.assertTrue(all("Ürün için test kancası" in row[2] for row in rows))
        self.assertTrue(all("trm-test" in row[3] for row in rows))

    def test_live_webhook_sends_campaign_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "distribution.db"
            self._create_approved_campaign(db_path, affiliate_status="partner_link")
            session = FakeSession()
            result = AutonomousDistributionEngine(
                db_path=db_path,
                mode="live",
                channels={"social_media": {"webhook_url": "https://hooks.example.test/campaign"}},
                session=session,
            ).distribute_processed({
                "kayitlar": [{"source_key": "affiliate-test-1", "durum": "submitted"}],
            })

        self.assertEqual(result["durum"], "completed")
        self.assertEqual(result["dagitilan"], 1)
        self.assertEqual(session.calls[0][0], "https://hooks.example.test/campaign")
        self.assertEqual(session.calls[0][1]["json"]["affiliate_url"], "https://trendurunlermarket.com/urun/trm-test?ref=test")

    def test_live_mode_skips_non_commissionable_fallback_traffic(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "distribution.db"
            self._create_approved_campaign(db_path)
            session = FakeSession()
            result = AutonomousDistributionEngine(
                db_path=db_path,
                mode="live",
                channels={"social_media": {"webhook_url": "https://hooks.example.test/campaign"}},
                session=session,
            ).distribute_processed({
                "kayitlar": [{"source_key": "affiliate-test-1", "durum": "submitted"}],
            })

        self.assertEqual(result["durum"], "error")
        self.assertEqual(result["dagitilan"], 0)
        self.assertIn("fallback", result["hatalar"][0]["error"])
        self.assertEqual(session.calls, [])

    def test_live_mode_rejects_unconfigured_channels(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "distribution.db"
            self._create_approved_campaign(db_path)
            result = AutonomousDistributionEngine(db_path=db_path, mode="live", channels={}).distribute_processed({
                "kayitlar": [{"source_key": "affiliate-test-1", "durum": "submitted"}],
            })

        self.assertEqual(result["durum"], "error")
        self.assertIn("kanal yapılandırılmalıdır", result["hatalar"][0]["error"])


if __name__ == "__main__":
    unittest.main()