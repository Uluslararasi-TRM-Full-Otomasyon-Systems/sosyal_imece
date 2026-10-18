import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dispatch_queue_manager import DispatchQueueManager
from oto_onarim_ajani import OtoOnarimAjani


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps({"status": "healthy", "service": "test-api"}).encode()


class OtoOnarimAjaniTests(unittest.TestCase):
    def test_healthy_api_and_queue_are_reported_without_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            DispatchQueueManager(str(db_path))
            agent = OtoOnarimAjani(queue_db=db_path)
            with patch("oto_onarim_ajani.socket.create_connection"), patch(
                "oto_onarim_ajani.urlopen", return_value=FakeResponse()
            ):
                report = agent.sistem_sagligini_tara_ve_onar()

        self.assertEqual(report["durum"], "healthy")
        self.assertFalse(report["onarim"]["gerceklestirildi"])
        self.assertTrue(all(check["status"] == "ok" for check in report["kontroller"]))

    def test_missing_database_is_reported_as_setup_not_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            agent = OtoOnarimAjani(queue_db=Path(directory) / "not-created.db")
            with patch("oto_onarim_ajani.socket.create_connection"), patch(
                "oto_onarim_ajani.urlopen", return_value=FakeResponse()
            ):
                report = agent.sistem_sagligini_tara_ve_onar()

        self.assertEqual(report["durum"], "needs_setup")
        self.assertEqual(report["kontroller"][-1]["status"], "not_initialized")

    def test_api_failure_is_reported_as_degraded_without_kill_or_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            agent = OtoOnarimAjani(queue_db=Path(directory) / "missing.db")
            with patch("oto_onarim_ajani.socket.create_connection", side_effect=OSError), patch(
                "oto_onarim_ajani.urlopen", side_effect=OSError
            ):
                report = agent.sistem_sagligini_tara_ve_onar()

        self.assertEqual(report["durum"], "degraded")
        self.assertFalse(report["onarim"]["gerceklestirildi"])

    def test_invalid_system_name_is_rejected(self):
        with self.assertRaises(ValueError):
            OtoOnarimAjani(sistem_adi=" ")

    def test_invalid_health_url_returns_degraded_report(self):
        agent = OtoOnarimAjani(health_url="not-a-url")

        report = agent.sistem_sagligini_tara_ve_onar()

        self.assertEqual(report["durum"], "degraded")
        self.assertEqual(report["kontroller"][1]["detail"], "Health URL geçersiz")


if __name__ == "__main__":
    unittest.main()