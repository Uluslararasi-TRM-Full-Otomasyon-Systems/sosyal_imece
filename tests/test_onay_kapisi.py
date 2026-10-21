# -*- coding: utf-8 -*-
"""Panel ONAY düğmesinin sunucu tarafı sözleşmesi (/api/izin_ver).

api_server_2 import edilirken aday taraması/WhatsApp/motor thread'leri ayağa
kalkar ve DB_PATH betiğin yanındaki canlı trm_veritabani.db'dir. Bu yüzden
import'dan ÖNCE tüm yan etkiler kapatılır, sonra veritabanı geçici bir dosyaya
çalınır: test canlı üssün verisine asla dokunmaz.
"""

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ["ADAY_TARAMA"] = "0"
os.environ["WHATSAPP_OTOMATIK_BASLAT"] = "0"
os.environ["OTONOM_GONDERIM"] = "0"
os.environ["OTONOM_GELEN_MESAJ"] = "0"
os.environ["OTONOM_OTOMATIK_YANIT"] = "0"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api_server_2 as servis  # noqa: E402


class OnayKapisiTestleri(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.yol = Path(self.tmp.name) / "t.db"
        conn = sqlite3.connect(self.yol)
        conn.execute(
            "CREATE TABLE esnaflar (id INTEGER PRIMARY KEY, isletme TEXT,"
            " telefon TEXT, kod TEXT UNIQUE, adres TEXT, durum TEXT DEFAULT 'ADAY',"
            " kayit_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.execute(
            "INSERT INTO esnaflar (id, isletme, telefon, kod, adres) VALUES"
            " (1, 'Zeytin Cafe', '0 (256) 612 99 65;+90 530 912 99 65', 'TRM-ZEY', 'Kusadasi'),"
            " (2, 'Ada Kirtasiye', '', 'TRM-ADA', 'Kusadasi')"
        )
        conn.commit()
        conn.close()
        self._goc()

        def baglan():
            c = sqlite3.connect(self.yol)
            c.row_factory = sqlite3.Row
            return c

        yama = mock.patch.object(servis, "veritabani_baglan", baglan)
        yama.start()
        self.addCleanup(yama.stop)
        self.c = servis.app.test_client()

    def _goc(self):
        conn = sqlite3.connect(self.yol)
        conn.row_factory = sqlite3.Row
        servis.sema_goc_uygula(conn)   # izin/opt_out + kara_liste + izin_log
        conn.commit()
        conn.close()

    def _izin(self, conn):
        return conn.execute("SELECT izin FROM esnaflar WHERE id = 1").fetchone()[0]

    def test_onay_izni_yazar_ve_denetim_kaydi_birakir(self):
        yanit = self.c.post("/api/izin_ver", json={"id": 1, "izin": 1})
        govde = yanit.get_json()
        self.assertEqual((yanit.status_code, govde["status"]), (200, "basarili"))
        self.assertEqual(govde["mobil"], "905309129965")
        conn = sqlite3.connect(self.yol)
        try:
            self.assertEqual(self._izin(conn), 1)
            self.assertEqual(
                conn.execute("SELECT izin, kaynak FROM izin_log").fetchall()[0][0], 1)
        finally:
            conn.close()

    def test_onay_cok_numarali_alanda_cep_redri_gorur(self):
        conn = sqlite3.connect(self.yol)
        conn.execute("INSERT INTO kara_liste (telefon, gerekce, tarih, kaynak)"
                     " VALUES ('905309129965', 'DUR yazdi', '2026-10-21 00:00:00', 'opt-out')")
        conn.commit()
        conn.close()
        yanit = self.c.post("/api/izin_ver", json={"id": 1, "izin": 1})
        self.assertEqual(yanit.status_code, 409)
        self.assertEqual(yanit.get_json()["mesaj"], "kara-liste")
        conn = sqlite3.connect(self.yol)
        try:
            self.assertEqual(self._izin(conn), 0, "red, onayi ezemez")
        finally:
            conn.close()

    def test_sabit_hatli_kayit_onaylanir_ama_panel_uyarir(self):
        conn = sqlite3.connect(self.yol)
        conn.execute("UPDATE esnaflar SET telefon = '+90 256 612 48 60' WHERE id = 1")
        conn.commit()
        conn.close()
        govde = self.c.post("/api/izin_ver", json={"id": 1}).get_json()
        self.assertTrue(govde["ok"])
        self.assertEqual(govde["mobil"], "")
        self.assertIn("mobil-degil", govde["uyari"])

    def test_onay_geri_alinir(self):
        self.c.post("/api/izin_ver", json={"id": 1, "izin": 1})
        govde = self.c.post("/api/izin_ver", json={"id": 1, "izin": 0}).get_json()
        self.assertEqual((govde["status"], govde["izin"], govde["onceki"]),
                         ("basarili", 0, 1))
        conn = sqlite3.connect(self.yol)
        try:
            self.assertEqual(self._izin(conn), 0)
        finally:
            conn.close()

    def test_gecersiz_id_ve_olmayan_kayit(self):
        self.assertEqual(self.c.post("/api/izin_ver", json={"id": "abc"}).status_code, 400)
        self.assertEqual(self.c.post("/api/izin_ver", json={}).status_code, 400)
        self.assertEqual(self.c.post("/api/izin_ver", json={"id": 999}).status_code, 404)

    def test_esnaflar_ucu_arayabilecegi_kaydi_ustu_getirir(self):
        govde = self.c.get("/api/esnaflar").get_json()
        self.assertEqual([k["id"] for k in govde], [1, 2])
        self.assertTrue(govde[0]["telefon_var"] and not govde[1]["telefon_var"])
        self.assertEqual(govde[0]["izin"], 0)
        self.assertEqual(govde[0]["mobil"], "905309129965")

    def test_aday_havuzu_telefonluyu_once_listeler(self):
        conn = sqlite3.connect(self.yol)
        conn.row_factory = sqlite3.Row
        try:
            kayitlar = servis.havuz_durumu(conn)["kayitlar"]
        finally:
            conn.close()
        self.assertEqual([k["isletme"] for k in kayitlar],
                         ["Zeytin Cafe", "Ada Kirtasiye"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
