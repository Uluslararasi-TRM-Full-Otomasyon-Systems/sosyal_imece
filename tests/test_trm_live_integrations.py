import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from magaza_api_koprusu import MagazaAPIBridge
from web_scraper import LiveWebScraper


class FakeResponse:
    def __init__(self, content=b"", body=None):
        self.content = content
        self._body = body or {}
        self.text = "ok"

    def raise_for_status(self):
        return None

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, response=None):
        self.response = response
        self.get_urls = []
        self.post_calls = []

    def get(self, url, **kwargs):
        self.get_urls.append(url)
        return self.response

    def post(self, url, **kwargs):
        self.post_calls.append((url, kwargs))
        if url.endswith("/oauth/token"):
            return FakeResponse(body={"access_token": "test-token"})
        return FakeResponse(body={"id": "store-product-1"})


class TrmLiveIntegrationTests(unittest.TestCase):
    def test_scraper_returns_dispatch_queue_json(self):
        response = FakeResponse(
            b"<rss><channel><item><title>Yeni trend</title><link>https://example.test/t</link>"
            b"<description>Trend aciklamasi</description></item></channel></rss>"
        )
        scraper = LiveWebScraper(
            sources=[{"name": "test-feed", "url": "https://example.test/rss"}],
            session=FakeSession(response),
        )

        queue_json = json.loads(scraper.fetch_trends_json())

        self.assertEqual(queue_json[0]["account_id"], "trm_live_web_scraper")
        self.assertEqual(queue_json[0]["payload"]["trend"]["title"], "Yeni trend")
        self.assertEqual(queue_json[0]["payload"]["status"], "pending_review")

    def test_bridge_simulates_only_approved_product_drafts(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            with closing(sqlite3.connect(db_path)) as connection:
                connection.execute(
                    "CREATE TABLE task_queue (id INTEGER PRIMARY KEY, account_id TEXT, post_id TEXT, payload TEXT, status TEXT, queued_at TEXT)"
                )
                connection.execute(
                    "INSERT INTO task_queue (post_id, payload, status) VALUES (?, ?, ?)",
                    ("approved-1", json.dumps({"task_type": "product_draft", "product": {"title": "Onayli urun"}}), "approved"),
                )
                connection.execute(
                    "INSERT INTO task_queue (post_id, payload, status) VALUES (?, ?, ?)",
                    ("pending-1", json.dumps({"task_type": "product_draft", "product": {"title": "Bekleyen urun"}}), "pending"),
                )
                connection.commit()
            session = FakeSession()

            result = MagazaAPIBridge(db_path=db_path, session=session).publish_approved_products()

        self.assertEqual(result["durum"], "completed")
        self.assertEqual([item["source_key"] for item in result["kayitlar"]], ["approved-1"])
        self.assertEqual(session.post_calls, [])

    def test_bridge_runs_oauth_then_posts_in_live_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            with closing(sqlite3.connect(db_path)) as connection:
                connection.execute(
                    "CREATE TABLE task_queue (id INTEGER PRIMARY KEY, account_id TEXT, post_id TEXT, payload TEXT, status TEXT, queued_at TEXT)"
                )
                connection.execute(
                    "INSERT INTO task_queue (post_id, payload, status) VALUES (?, ?, ?)",
                    ("approved-1", json.dumps({"task_type": "product_draft", "product": {"title": "Test product"}}), "approved"),
                )
                connection.commit()
            session = FakeSession()

            result = MagazaAPIBridge(
                db_path=db_path,
                api_base_url="https://api.example.test/v1",
                token_url="https://api.example.test/oauth/token",
                client_id="client",
                client_secret="secret",
                simulate=False,
                session=session,
            ).publish_approved_products()

            with closing(sqlite3.connect(db_path)) as connection:
                saved_status = connection.execute(
                    "SELECT status FROM magaza_api_submissions WHERE source_key = ?", ("approved-1",)
                ).fetchone()[0]

        self.assertEqual(result["gonderilen"], 1)
        self.assertEqual(saved_status, "submitted")
        self.assertEqual([call[0] for call in session.post_calls], [
            "https://api.example.test/oauth/token",
            "https://api.example.test/v1/products",
        ])
        self.assertEqual(session.post_calls[1][1]["headers"]["Authorization"], "Bearer test-token")

    def test_bridge_does_not_live_post_fallback_redirects(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            with closing(sqlite3.connect(db_path)) as connection:
                connection.execute(
                    "CREATE TABLE task_queue (id INTEGER PRIMARY KEY, account_id TEXT, post_id TEXT, payload TEXT, status TEXT, queued_at TEXT)"
                )
                connection.execute(
                    "INSERT INTO task_queue (post_id, payload, status) VALUES (?, ?, ?)",
                    (
                        "fallback-1",
                        json.dumps({
                            "task_type": "gelir_getiren_gorev",
                            "etiket": "gelir_getiren_gorev",
                            "status": "approved",
                            "affiliate_link_status": "fallback_redirect",
                            "product": {"title": "Test product"},
                        }),
                        "approved",
                    ),
                )
                connection.commit()
            session = FakeSession()

            result = MagazaAPIBridge(
                db_path=db_path,
                api_base_url="https://api.example.test/v1",
                client_id="client",
                client_secret="secret",
                token_url="https://api.example.test/oauth/token",
                simulate=False,
                session=session,
            ).publish_approved_products()

        self.assertEqual(result["durum"], "partial_error")
        self.assertEqual(result["gonderilen"], 0)
        self.assertIn("fallback", result["hatalar"][0]["error"])
        self.assertEqual(session.post_calls, [])

    def test_environment_live_request_fails_closed_without_store_endpoint_and_auth(self):
        session = FakeSession()
        with patch.dict("os.environ", {
            "TRM_MAGAZA_API_ENABLED": "1",
            "TRM_STORE_SIMULATE": "0",
        }, clear=True):
            result = MagazaAPIBridge(
                db_path="unused-test-queue.db",
                session=session,
            ).publish_approved_products()

        self.assertEqual(result["durum"], "error")
        self.assertFalse(result["simulasyon"])
        self.assertEqual(session.post_calls, [])
        self.assertIn("TRM_STORE_API_BASE_URL", result["hatalar"][0]["error"])


if __name__ == "__main__":
    unittest.main()