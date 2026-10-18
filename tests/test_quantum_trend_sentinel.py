import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quantum_trend_sentinel import QuantumTrendSentinel, kuyruğa_ekle


class QuantumTrendSentinelTests(unittest.TestCase):
    def test_scan_marks_the_result_as_simulated(self):
        sentinel = QuantumTrendSentinel(hedef_pazar="US/EU", rng=Random(0))

        trend = sentinel.sosyal_dalga_tara()

        self.assertEqual(trend["hedef_pazar"], "US/EU")
        self.assertEqual(trend["sinyal_kaynagi"], "simülasyon")
        self.assertIn("urun_adi", trend)
        self.assertIn("tarama_zamani", trend)

    def test_scan_rejects_empty_market_and_empty_trend_list(self):
        with self.assertRaises(ValueError):
            QuantumTrendSentinel(hedef_pazar=" ")
        with self.assertRaises(ValueError):
            QuantumTrendSentinel(trendler=[]).sosyal_dalga_tara()

    def test_queue_adds_review_task_as_pending(self):
        trend = QuantumTrendSentinel(rng=Random(0)).sosyal_dalga_tara()
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            task = kuyruğa_ekle(trend, db_path=db_path)

            connection = sqlite3.connect(db_path)
            try:
                row = connection.execute(
                    "SELECT account_id, post_id, status FROM task_queue"
                ).fetchone()
            finally:
                connection.close()

        self.assertEqual(row, ("quantum_trend_sentinel", task["post_id"], "pending"))
        self.assertEqual(task["payload"]["status"], "pending_review")

    def test_queue_rejects_invalid_trend(self):
        with self.assertRaises(ValueError):
            kuyruğa_ekle({})


if __name__ == "__main__":
    unittest.main()