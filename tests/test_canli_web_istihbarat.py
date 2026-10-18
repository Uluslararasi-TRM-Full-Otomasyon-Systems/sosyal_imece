import sqlite3
import os
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from canli_web_istihbarat import CanliWebIstihbaratCeviricisi, PublicTargetError


class FakeResponse:
    def __init__(self, body=b"", status_code=200, content_type="text/html"):
        self.body = body
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
        self.encoding = "utf-8"

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def iter_content(self, chunk_size):
        yield self.body


class CanliWebIstihbaratTests(unittest.TestCase):
    def test_extracts_up_to_three_hacker_news_titles(self):
        html = """<span class='titleline'><a>First</a></span>
        <span class='titleline'><a>Second</a></span>
        <span class='titleline'><a>Third</a></span>
        <span class='titleline'><a>Fourth</a></span>"""
        self.assertEqual(
            CanliWebIstihbaratCeviricisi._extract_headlines(html),
            ["First", "Second", "Third"],
        )

    def test_public_scan_stores_results_as_pending_review(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "intel.db"
            scraper = CanliWebIstihbaratCeviricisi(db_path)
            response = FakeResponse(b"<span class='titleline'><a>Headline</a></span>")
            with patch.object(scraper, "_robots_allowed", return_value=True), patch(
                "canli_web_istihbarat.requests.get", return_value=response
            ), patch.object(scraper, "_validate_public_url", return_value=Mock(scheme="https", netloc="example.com")):
                result = scraper.web_taramasi_yap("https://example.com/")

            connection = sqlite3.connect(db_path)
            try:
                row = connection.execute(
                    "SELECT kaynak_url, baslik, durum FROM canli_istihbarat"
                ).fetchone()
            finally:
                connection.close()

        self.assertEqual(result["durum"], "draft_ready")
        self.assertEqual(row, ("https://example.com/", "Headline", "pending_review"))

    def test_private_targets_are_rejected(self):
        with patch("canli_web_istihbarat.socket.getaddrinfo") as resolver:
            resolver.return_value = [(None, None, None, None, ("127.0.0.1", 443))]
            with self.assertRaises(PublicTargetError):
                CanliWebIstihbaratCeviricisi._validate_public_url("https://localhost/")

    def test_non_http_schemes_and_redirects_are_rejected(self):
        with self.assertRaises(PublicTargetError):
            CanliWebIstihbaratCeviricisi._validate_public_url("file:///etc/passwd")
        with tempfile.TemporaryDirectory() as directory:
            scraper = CanliWebIstihbaratCeviricisi(Path(directory) / "intel.db")
            response = FakeResponse(status_code=302)
            with patch.object(scraper, "_validate_public_url", return_value=Mock()), patch(
                "canli_web_istihbarat.requests.get", return_value=response
            ):
                with self.assertRaises(PublicTargetError):
                    scraper._fetch_text("https://example.com/")

    def test_streamlit_scan_saves_mocked_headline_for_review(self):
        from streamlit.testing.v1 import AppTest

        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "ui-intel.db"
            previous_db = os.environ.get("TRM_LIVE_INTEL_DB")
            os.environ["TRM_LIVE_INTEL_DB"] = str(db_path)
            try:
                with ExitStack() as stack:
                    stack.enter_context(patch.object(
                        CanliWebIstihbaratCeviricisi,
                        "_robots_allowed",
                        return_value=True,
                    ))
                    stack.enter_context(patch.object(
                        CanliWebIstihbaratCeviricisi,
                        "_fetch_text",
                        return_value=(
                            urlparse("https://news.ycombinator.com/"),
                            "<span class='titleline'><a>Test headline</a></span>",
                        ),
                    ))
                    app = AppTest.from_file(
                        str(Path(__file__).resolve().parents[1] / "run.py"),
                        default_timeout=30,
                    ).run()
                    app.selectbox(key="module_nav").select("Canlı web istihbaratı").run()
                    app.button[0].click().run()
                    self.assertFalse(app.exception)
                    self.assertTrue(app.success)
            finally:
                if previous_db is None:
                    os.environ.pop("TRM_LIVE_INTEL_DB", None)
                else:
                    os.environ["TRM_LIVE_INTEL_DB"] = previous_db

            connection = sqlite3.connect(db_path)
            try:
                row = connection.execute(
                    "SELECT baslik, durum FROM canli_istihbarat"
                ).fetchone()
            finally:
                connection.close()
        self.assertEqual(row, ("Test headline", "pending_review"))


if __name__ == "__main__":
    unittest.main()