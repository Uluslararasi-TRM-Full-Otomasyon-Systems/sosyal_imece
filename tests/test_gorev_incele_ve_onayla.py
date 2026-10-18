import ast
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gorev_incele_ve_onayla import autonomous_approve_and_transfer, load_pending_tasks


class GorevInceleVeOnaylaTests(unittest.TestCase):
    def test_autonomy_fills_missing_link_approves_and_transfers_legacy_task(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            task = {
                "account_id": "trm_hizli_kazanc",
                "post_id": "affiliate-test-1",
                "payload": {
                    "task_type": "gelir_getiren_gorev",
                    "etiket": "gelir_getiren_gorev",
                    "status": "pending_review",
                    "product": {"title": "Test product"},
                    "social_media_hooks": ["Test hook"],
                },
            }
            with closing(sqlite3.connect(db_path)) as connection:
                connection.execute(
                    "CREATE TABLE task_queue (id INTEGER PRIMARY KEY, account_id TEXT, post_id TEXT, payload TEXT, status TEXT, queued_at TEXT)"
                )
                connection.execute(
                    "INSERT INTO task_queue (account_id, post_id, payload, status, queued_at) VALUES (?, ?, ?, ?, ?)",
                    (task["account_id"], task["post_id"], repr(task), "pending", "test"),
                )
                connection.commit()

            pending = load_pending_tasks(db_path)
            self.assertEqual(len(pending), 1)
            report = autonomous_approve_and_transfer(db_path)

            with closing(sqlite3.connect(db_path)) as connection:
                row = connection.execute(
                    "SELECT payload, status FROM task_queue WHERE post_id = ?",
                    (task["post_id"],),
                ).fetchone()
            stored_task = ast.literal_eval(row[0])
            self.assertEqual(row[1], "approved")
            self.assertEqual(stored_task["payload"]["status"], "approved")
            self.assertEqual(stored_task["payload"]["approval_status"], "approved")
            self.assertEqual(stored_task["payload"]["affiliate_link_status"], "fallback_redirect")
            self.assertTrue(stored_task["payload"]["affiliate_link_draft"].startswith("https://"))

        self.assertEqual(report["durum"], "completed")
        self.assertEqual(report["onaylanan"], 1)
        self.assertEqual(report["magaza_koprusu"]["kayitlar"][0]["source_key"], "affiliate-test-1")
        self.assertEqual(report["magaza_koprusu"]["kayitlar"][0]["durum"], "simulated")
        self.assertEqual(report["dagitim"]["dagitilan"], 3)
        self.assertEqual(report["dagitim"]["durum"], "completed")

    def test_live_readiness_block_leaves_pending_task_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            task = {
                "account_id": "trm_hizli_kazanc",
                "post_id": "affiliate-blocked-1",
                "payload": {
                    "task_type": "gelir_getiren_gorev",
                    "etiket": "gelir_getiren_gorev",
                    "status": "pending_review",
                    "product": {"title": "Test product"},
                    "social_media_hooks": ["Test hook"],
                },
            }
            with closing(sqlite3.connect(db_path)) as connection:
                connection.execute(
                    "CREATE TABLE task_queue (id INTEGER PRIMARY KEY, account_id TEXT, post_id TEXT, payload TEXT, status TEXT, queued_at TEXT)"
                )
                connection.execute(
                    "INSERT INTO task_queue (account_id, post_id, payload, status, queued_at) VALUES (?, ?, ?, ?, ?)",
                    (task["account_id"], task["post_id"], repr(task), "pending", "test"),
                )
                connection.commit()

            with patch.dict(os.environ, {}, clear=True):
                report = autonomous_approve_and_transfer(
                    db_path,
                    live_store=True,
                    distribution_mode="live",
                    distribution_channels={},
                )

            with closing(sqlite3.connect(db_path)) as connection:
                queue_status = connection.execute(
                    "SELECT status FROM task_queue WHERE post_id = ?",
                    (task["post_id"],),
                ).fetchone()[0]

        self.assertEqual(report["durum"], "blocked")
        self.assertEqual(queue_status, "pending")
        self.assertTrue(report["live_readiness"]["missing"])


if __name__ == "__main__":
    unittest.main()
