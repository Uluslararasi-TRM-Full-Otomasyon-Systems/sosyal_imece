import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("WHATSAPP_OTOMATIK_BASLAT", "0")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from esnaf_sablonu import SABLON, SablonHatasi, esnaf_tanitim_metni

BEKLENEN = (
    "Sayın Ahmet Yılmaz Hanım veya bey\n"
    "Kahve Duraadı dükkanınızı Kuşadası'ndaki nokta hedef kitleye doğrudan "
    "ulaştırmak için TRM Ekosistemi olarak yanınızdayız.\n"
    "📍 Adresiniz: Atatürk Cad. No:12 Kuşadası\n"
    "🎯 Nokta Atışı Tanıtım: İşletmenizin kalitesini ve hizmetlerini sosyal medya "
    "kanallarımızda doğrudan hedef kitlenize tanıtıyoruz.\n"
    "🔒 TRM Nirvana Güvenlik & Doğrulama Sistemi: Kasaya gelen müşteriden 4 haneli "
    "SMS/Anlık Onay Kodu istenir (Örn: TRM-3126). Kod esnaf paneline girildiğinde "
    "Ad-Soyad, T.C. ve GSM doğrulaması anlık yapılır. Suistimal ve kaçaklara karşı "
    "%100 güvenlidir.\n"
    "🎁 İlk 5 Müşteri Yönlendirmesi Sıfır Komisyon! Sistemi canlı görmeniz için ilk "
    "5 yönlendirmede 1 TL bile talep etmiyoruz.\n"
    "Uygun olduğunuzda dükkanınıza bir çayınızı içmeye gelelim mi?\n"
    "Bu mesajları almak istemiyorsanız yanıt olarak 'DUR' yazmanız yeterli: "
    "numaranız kalıcı olarak listemizden çıkar ve bir daha yazmayız."
)


class AliciDogrulamaTestleri(unittest.TestCase):
    def setUp(self):
        from api_server_2 import _kimlik_eslesir_mi
        self.eslesir = _kimlik_eslesir_mi

    def test_numara_bicimlari_tanimanir(self):
        for baslik in ("0530 000 00 00", "+90 530 000 00 00", "905300000000",
                       "Test Isletmesi (0530 000 00 00)"):
            with self.subTest(baslik=baslik):
                self.assertTrue(self.eslesir(baslik, "905300000000", "Test Isletmesi"))

    def test_baska_acik_sohbet_reddedilir(self):
        self.assertFalse(self.eslesir("Yakın Sohbet", "905300000000", "Test Isletmesi"))
        self.assertFalse(self.eslesir("", "905300000000", "Test Isletmesi"))

    def test_kayitli_rehber_adi_ile_eslesir(self):
        self.assertTrue(self.eslesir("Zeytin Café", "905300000000", "zeytin cafe"))


class EsnafSablonuTestleri(unittest.TestCase):
    def test_metin_kilidi_birebir_ayni(self):
        metin = esnaf_tanitim_metni(
            "Kahve Duraadı", "Atatürk Cad. No:12 Kuşadası", "Ahmet Yılmaz"
        )
        self.assertEqual(metin, BEKLENEN)

    def test_sablon_yedi_satir_ve_emoji_korunur(self):
        self.assertEqual(len(SABLON.splitlines()), len(BEKLENEN.splitlines()))
        for sembol in ("📍", "🎯", "🔒", "🎁"):
            self.assertIn(sembol, esnaf_tanitim_metni("X", "Y"))

    def test_dinamik_alanlar_satir_uzatmadan_oturur(self):
        metin = esnaf_tanitim_metni("  Süper   Market  ", "Cumhuriyet Cad.\nNo:5\nKuşadası")
        self.assertIn("Süper Market dükkanınızı", metin)
        self.assertIn("📍 Adresiniz: Cumhuriyet Cad. No:5 Kuşadası", metin)
        self.assertEqual(len(metin.splitlines()), len(BEKLENEN.splitlines()))

    def test_yetkili_bos_ise_varsayilan_selamlama(self):
        self.assertTrue(
            esnaf_tanitim_metni("X", "Y", "   ").startswith("Sayın Yetkili Hanım veya bey")
        )

    def test_zorunlu_alan_eksikken_gonderim_engellenir(self):
        for isletme, adres in ((("", "Adres"), ("İşletme", ""), ("", None))):
            with self.assertRaises(SablonHatasi) as hata:
                esnaf_tanitim_metni(isletme, adres)
            self.assertTrue(hata.exception.eksikler)

    def test_yer_tutucu_kalintisi_yok(self):
        self.assertNotIn("[", esnaf_tanitim_metni("X", "Y", "Z"))


class HedefSohbetKapisiTestleri(unittest.TestCase):
    """_hedef_sohbeti_ac: metin yazılmadan önce alıcının kendisi doğrulanmalı."""

    def setUp(self):
        from unittest import mock

        from api_server_2 import _hedef_sohbeti_ac
        self.ac = _hedef_sohbeti_ac
        uyku = mock.patch("time.sleep", lambda *_: None)
        uyku.start()
        self.addCleanup(uyku.stop)

    def _taklit(self, baslik, arama_sonucu=None):
        from selenium.common.exceptions import WebDriverException

        class Surucu:
            aktif = baslik

            def find_element(self, *a, **k):
                raise WebDriverException("yok")

            def find_elements(self, *a, **k):
                return []

            def execute_script(self, js, *args):
                if "conversation-header" in js:
                    return self.aktif
                if "return trmAramaKutusu();" in js:
                    return "kutu" if arama_sonucu else None
                if "trmAramaKutusu();" in js:
                    return bool(arama_sonucu)
                if "listitem" in js:
                    if "click()" in js:
                        self.aktif = arama_sonucu or self.aktif
                        return True
                    return arama_sonucu or ""
                return ""

        return Surucu()

    def test_baska_sohbet_aciksa_gonderime_izin_yok(self):
        ok, kimlik = self.ac(
            self._taklit("Yakın Sohbet"), "905300000000", "Test Isletmesi", süre=0.05
        )
        self.assertFalse(ok)
        self.assertEqual(kimlik, "Yakın Sohbet")

    def test_numara_baslikta_izlenirse_sohbet_acik_sayilir(self):
        ok, kimlik = self.ac(
            self._taklit("+90 542 623 51 16 (Siz)"), "905426235116", "TRM", süre=0.05
        )
        self.assertTrue(ok)
        self.assertIn("542 623 51 16", kimlik)

    def test_aramada_cikan_baslik_sohbeti_acar(self):
        surucu = self._taklit("Yakın Sohbet", arama_sonucu="Zeytin Cafe")
        ok, kimlik = self.ac(surucu, "905370000000", "Başka İşletme", süre=0.05)
        self.assertTrue(ok)
        self.assertEqual(kimlik, "Zeytin Cafe")


class MetinKilidiTestleri(unittest.TestCase):
    """Gönderimden hemen önce composer'daki metin şablonla birebir olmalı."""

    def setUp(self):
        from api_server_2 import _metin_kilidi_kontrol
        self.kontrol = _metin_kilidi_kontrol
        self.metin = esnaf_tanitim_metni("TRM Hat İçi Test", "Kuşadası, Aydın", "Qoder")

    def _surucu(self, kutu_metni):
        class Surucu:
            def execute_script(self, js, *args):
                return kutu_metni if "contenteditable" in js else None

        return Surucu()

    def test_whatsapp_blok_ayraci_cizgi_sayilmaz(self):
        # Composer her satırı <p> ile veriyor; innerText satır aralarında \n\n üretir.
        kutu = "\n\n".join(self.metin.splitlines())
        self.assertEqual(self.kontrol(self._surucu(kutu), self.metin), (True, ""))

    def test_satir_sonlari_kaybolursa_gonderim_durur(self):
        kutu = " ".join(self.metin.splitlines())
        tamam, sebep = self.kontrol(self._surucu(kutu), self.metin)
        self.assertFalse(tamam)
        self.assertIn("satır sayısı", sebep)

    def test_baska_metin_yazilirsa_gonderim_durur(self):
        tamam, sebep = self.kontrol(self._surucu(self.metin + " EK"), self.metin)
        self.assertFalse(tamam)
        self.assertIn("birebir", sebep)

    def test_composer_yoksa_gonderim_durur(self):
        self.assertEqual(self.kontrol(self._surucu(None), self.metin),
                         (False, "mesaj kutusu bulunamadı"))


class TeslimatKaydiTestleri(unittest.TestCase):
    """Panel geçmişi yalnızca WhatsApp teslimatı onaylandığında yazılmalı."""

    def setUp(self):
        import sqlite3
        import tempfile
        from unittest import mock

        import api_server_2 as servis
        self.servis = servis
        self.sqlite3 = sqlite3
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.yol = Path(self.tmp.name) / "t.db"
        conn = sqlite3.connect(self.yol)
        conn.execute(
            "CREATE TABLE esnaflar (id INTEGER PRIMARY KEY, isletme TEXT,"
            " telefon TEXT, adres TEXT, yetkili TEXT)"
        )
        conn.execute(
            "INSERT INTO esnaflar VALUES (7, 'Zeytin Cafe', '905370000000',"
            " 'Kuşadası', 'Ayşe')"
        )
        conn.commit()
        conn.close()
        self.addCleanup(self.tmp.cleanup)

        def baglan():
            conn = sqlite3.connect(self.yol)
            conn.row_factory = sqlite3.Row
            return conn

        bag = mock.patch.object(servis, "veritabani_baglan", baglan)
        bag.start()
        self.addCleanup(bag.stop)
        yamayi = mock.patch.object(servis, "gercek_whatsapp_mesaj_gonder")
        self.gonderim_mock = yamayi.start()
        self.addCleanup(yamayi.stop)

    def _kayitlar(self):
        conn = self.sqlite3.connect(self.yol)
        try:
            return conn.execute("SELECT gonderen, mesaj FROM mesajlar").fetchall()
        except self.sqlite3.OperationalError:
            return []
        finally:
            conn.close()

    def test_gonderilemeyen_mesaj_gecmise_dusmez(self):
        self.gonderim_mock.return_value = False
        govde, kod = self.servis._esnaf_tanitimi_gonder(7)
        self.assertEqual((kod, govde["status"]), (200, "gonderilemedi"))
        self.assertEqual(self._kayitlar(), [])

    def test_teslim_edilen_mesaj_kaydedilir(self):
        self.gonderim_mock.return_value = True
        govde, kod = self.servis._esnaf_tanitimi_gonder(7)
        self.assertEqual((kod, govde["status"]), (200, "basarili"))
        self.assertEqual(self._kayitlar(), [("DERYA", govde["metin"])])

    def _serbest_yanit(self, teslim):
        from unittest import mock
        self.gonderim_mock.return_value = teslim
        yanitla = mock.patch.object(self.servis, "derya_otonom_yanitla",
                                    lambda *a, **k: "Çay içmeye geliyoruz.")
        yanitla.start()
        self.addCleanup(yanitla.stop)
        istemci = self.servis.app.test_client()
        return istemci.post(
            "/api/mesaj_gonder",
            json={"esnaf_id": 7, "mesaj": "Merhaba, sistem nasıl çalışıyor?"},
        )

    def test_serbest_yanit_yalnizca_teslim_edilince_kayit(self):
        self.assertEqual(self._serbest_yanit(False).status_code, 200)
        self.assertEqual(self._kayitlar(),
                         [("ESNAF", "Merhaba, sistem nasıl çalışıyor?")])

    def test_serbest_yanit_teslim_edilince_kayit(self):
        self.assertEqual(self._serbest_yanit(True).status_code, 200)
        self.assertEqual(self._kayitlar(), [
            ("ESNAF", "Merhaba, sistem nasıl çalışıyor?"),
            ("DERYA", "Çay içmeye geliyoruz."),
        ])


class GonderimYoluSablonTestleri(unittest.TestCase):
    """Selenium/API sözleşmesi: sessizce ölen çağrılar bir daha girmesin."""

    def setUp(self):
        import api_server_2 as servis
        self.servis = servis
        self.kaynak = Path(servis.__file__).read_text(encoding="utf-8")

    def test_keys_chord_yok(self):
        # Selenium 4.47'de Keys.chord yok: AttributeError gönderimi sessizce bozar.
        for satir in self.kaynak.splitlines():
            if satir.lstrip().startswith("#"):
                continue
            self.assertNotIn("Keys.chord(", satir)

    def test_arama_js_bileşimi(self):
        self.assertEqual(
            self.servis._ARAMA_KUTUSU_BUL_JS.count("function trmAramaKutusu()"), 1
        )
        self.assertTrue(
            self.servis._ARAMA_YAZ_JS.startswith(self.servis._ARAMA_KUTUSU_BUL_JS)
        )
        for js in (self.servis._ARAMA_KUTUSU_JS, self.servis._ARAMA_YAZ_JS):
            self.assertEqual(js.count("{"), js.count("}"), js[:60])


class EsnafEslestirmeTestleri(unittest.TestCase):
    """Aday havuzundaki scraped isimler kişisel sohbetlerle eşleşmemeli."""

    def setUp(self):
        import sqlite3
        import tempfile

        import api_server_2 as servis
        self.servis = servis
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.yol = Path(self.tmp.name) / "eslestirme.db"
        self.sqlite3 = sqlite3
        self.addCleanup(self.tmp.cleanup)
        self._kur("Zeytin Cafe", "905370000000", durum="onayli", izin=0)

    def _kur(self, isletme, telefon, durum, izin, id=7):
        """Tabloyu istenen satırla (yeniden) kur + eşleştirme bağlantısı döndür."""
        self.sqlite3.connect(self.yol).close()
        conn = self.sqlite3.connect(self.yol)
        conn.execute("DROP TABLE IF EXISTS esnaflar")
        conn.execute(
            "CREATE TABLE esnaflar (id INTEGER PRIMARY KEY, isletme TEXT,"
            " telefon TEXT, durum TEXT, izin INTEGER)"
        )
        conn.execute("INSERT INTO esnaflar VALUES (?, ?, ?, ?, ?)",
                     (id, isletme, telefon, durum, izin))
        conn.commit()
        conn.close()

    def _eslestir(self, baslik):
        conn = self.sqlite3.connect(self.yol)
        conn.row_factory = self.sqlite3.Row
        try:
            return self.servis._esnaf_eslestir(conn, baslik)
        finally:
            conn.close()

    def test_aday_isimi_kisisel_sohbet_basligiyla_cakisisirsa_esnaf_sayilmaz(self):
        self._kur("Zeytin Cafe", "", durum="ADAY", izin=0)
        self.assertIsNone(self._eslestir("Zeytin Cafe Çocukları WhatsApp Grubu"))

    def test_aday_numarasi_da_kisisel_sohbette_esnaf_sayilmaz(self):
        self._kur("Zeytin Cafe", "905370000000", durum="ADAY", izin=0)
        self.assertIsNone(self._eslestir("+90 537 000 00 00"))

    def test_onayli_kayit_eslesir(self):
        self.assertEqual(self._eslestir("Zeytin Cafe - Sipariş"), 7)

    def test_operator_izin_verince_aday_tekrar_eslesilebilir(self):
        self._kur("Zeytin Cafe", "905370000000", durum="ADAY", izin=1)
        self.assertEqual(self._eslestir("Zeytin Cafe"), 7)


if __name__ == "__main__":
    unittest.main()
