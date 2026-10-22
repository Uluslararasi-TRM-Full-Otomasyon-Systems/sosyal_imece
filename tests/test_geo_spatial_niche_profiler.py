import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from geo_spatial_niche_profiler import GeoSpatialNicheProfiler

_FIRSAT = [{"bolge": "Kuşadası / Sahil", "tespit_edilen_niche": "Taşınbilir fan",
            "anlik_faktor": "OSM POI yoğunluğu", "tavsiye_edilen_aksiyon": "içerik taslağı"}]


class GeoSpatialNicheProfilerTests(unittest.TestCase):
    def test_veri_saglanmayinca_hicbir_nis_uydurulmaz(self):
        report = GeoSpatialNicheProfiler().bolgesel_niche_tara()

        self.assertEqual(report["durum"], "not_configured")
        self.assertIsNone(report["tespit_edilen_niche"])
        self.assertFalse(report["canli_hava_ve_koordinat_verisi"])
        self.assertIn("firsatlar", report["sebep"])

    def test_saglanan_gercek_kayit_eslesir(self):
        report = GeoSpatialNicheProfiler(
            hedef_bolge="Kuşadası / Akdeniz Havzası", firsatlar=_FIRSAT
        ).bolgesel_niche_tara()

        self.assertEqual(report["durum"], "ok")
        self.assertIn("Kuşadası", report["bolge"])
        self.assertEqual(report["veri_kaynagi"], "sağlanan bölgesel veri")

    def test_eslesmeyen_bolge_red_verir(self):
        report = GeoSpatialNicheProfiler(hedef_bolge="Hakkari", firsatlar=_FIRSAT) \
            .bolgesel_niche_tara()
        self.assertEqual(report["durum"], "not_configured")

    def test_dogrulanmamis_rapor_kuyruga_yazilamaz(self):
        profiler = GeoSpatialNicheProfiler()
        rapor = profiler.bolgesel_niche_tara()
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            with self.assertRaises(ValueError):
                profiler.inceleme_kuyruguna_ekle(rapor, db_path=db_path)
            self.assertFalse(db_path.exists(), "red edilen rapor kuyruk dosyası oluşturamaz")

    def test_aydinlatilmis_rapor_kuyruga_pending_yazar(self):
        profiler = GeoSpatialNicheProfiler(firsatlar=_FIRSAT)
        report = profiler.bolgesel_niche_tara()
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "queue.db"
            task = profiler.inceleme_kuyruguna_ekle(report, db_path=db_path)
            connection = sqlite3.connect(db_path)
            try:
                row = connection.execute(
                    "SELECT account_id, post_id, status FROM task_queue"
                ).fetchone()
            finally:
                connection.close()

        self.assertEqual(row, ("geo_spatial_niche_profiler", task["post_id"], "pending"))
        self.assertEqual(task["payload"]["status"], "pending_review")

    def test_gecersiz_bolge_ve_rapor_reddedilir(self):
        with self.assertRaises(ValueError):
            GeoSpatialNicheProfiler(hedef_bolge=" ")
        with self.assertRaises(ValueError):
            GeoSpatialNicheProfiler(firsatlar=_FIRSAT).inceleme_kuyruguna_ekle({})


if __name__ == "__main__":
    unittest.main()
