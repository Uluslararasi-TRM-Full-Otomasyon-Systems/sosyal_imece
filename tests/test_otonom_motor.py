# -*- coding: utf-8 -*-
"""otonom_motor.py testleri — Chrome/Selenium BAŞLATDAN çalışır.

Motor, gönderme ve oturum yoklaması callback olarak enjekte edildiği için bu
testler geçici bir SQLite dosyası üzerinde tam döngüyü doğrular. pytest ile ya
da `python tests/test_otonom_motor.py` (bağımlılıksız) koşulabilir.
"""

import os
import sys
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import otonom_motor as m  # noqa: E402

# Canlı testlerde her zaman pencere içinde kalalım (pencere kendi testinde denenir).
TUR = datetime(2026, 10, 19, 12, 0, 0, tzinfo=timezone.utc)

_ANA_SEMA = (
    "CREATE TABLE esnaflar (id INTEGER PRIMARY KEY AUTOINCREMENT, isletme TEXT, "
    "telefon TEXT, kod TEXT UNIQUE, adres TEXT, durum TEXT DEFAULT GÖNDERİLDİ, "
    "gelen_yanit TEXT, kayit_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP, "
    "durum_kilit INTEGER DEFAULT 0)"
)


def _veritabani():
    fd, yol = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(yol)
    conn.row_factory = sqlite3.Row
    conn.execute(_ANA_SEMA)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS mesajlar (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "esnaf_id INTEGER, gonderen TEXT, mesaj TEXT, tarih DATETIME DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    return conn, yol


def _kayit_ekle(conn, **kw):
    alanlar = {
        "isletme": "Test Dukkan", "telefon": "905300000000", "kod": None,
        "adres": "Kusadasi, test mah.", "durum": "onayli",
    }
    alanlar.update(kw)
    if alanlar["kod"] is None:
        alanlar["kod"] = "TRM-" + str(alanlar["telefon"])[-4:] + "-" + str(os.urandom(2).hex())
    conn.execute(
        "INSERT INTO esnaflar (isletme, telefon, kod, adres, durum) VALUES (?,?,?,?,?)",
        (alanlar["isletme"], alanlar["telefon"], alanlar["kod"], alanlar["adres"], alanlar["durum"]),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]


def _yapi(**env):
    e = {k: str(v) for k, v in env.items()}
    e.setdefault("OTONOM_GONDERIM", "0")
    return m.Yapilandirma(e)


def _motor(conn, yapi, gonder=None, oturum=True, kayitlar=None, aralar=None):
    """Motor her turda KENDI baglantisi ile calisir ve onu kapatir (uretimdeki
    veritabani_baglan() sozlesmesi). Testin kendi conn'i bu yuzden yol uzerinden
    yeni baglanti acmali; yoksa 'Cannot operate on a closed database' aliriz."""
    if isinstance(conn, str):
        yol = conn
    else:
        yol = conn.execute("PRAGMA database_list").fetchone()[2]

    def baglan():
        if not yol:
            conn.row_factory = sqlite3.Row
            return conn
        c = sqlite3.connect(yol)
        c.row_factory = sqlite3.Row
        return c

    def _gonder(esnaf_id):
        (kayitlar if kayitlar is not None else []).append(esnaf_id)
        return {"status": "basarili", "esnaf_id": esnaf_id}

    return m.Motor(
        yapi, baglan, gonder or _gonder,
        lambda: oturum, lambda sn: (aralar if aralar is not None else []).append(sn),
        lambda mesaj: None, simdi=lambda: TUR,
    )


# ---------------------------------------------------------------------------
def test_goc_idempotent_ve_veri_korunur():
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn, isletme="Bayat Dukkan")
        eklenen = m.sema_goc_uygula(conn)
        assert "izin" in eklenen and "gonderim_durumu" in eklenen
        m.sema_goc_uygula(conn)  # ikinci kez: hata olmamalı, kolon listesi boş
        assert m.sema_goc_uygula(conn) == []
        row = conn.execute("SELECT isletme, izin, gonderim_durumu FROM esnaflar WHERE id=?",
                           (id1,)).fetchone()
        assert row["isletme"] == "Bayat Dukkan"
        assert row["izin"] == 0, "izin varsayilan 0 olmali (fail-closed)"
        assert row["gonderim_durumu"] == m.HAZIR
        assert "kiralama_zamani" in m.mevcut_kolonlar(conn)
    finally:
        conn.close(); os.unlink(yol)


def test_kapali_mod_hicbir_gonderim_ve_hicbir_yazma_yapmaz():
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn)
        m.sema_goc_uygula(conn)
        conn.execute("UPDATE esnaflar SET izin = 1 WHERE id = ?", (id1,))
        conn.commit()
        denenmis, aralar = [], []
        motor = _motor(conn, _yapi(OTONOM_GONDERIM="0"), kayitlar=denenmis, aralar=aralar)
        sonuc = motor.bir_tur()
        assert sonuc["mod"] == "kapali"
        assert sonuc["gonderilen"] == 0
        assert sonuc["aday_id"] == [id1], "aday listesi gorunur ama gonderilmez"
        assert denenmis == [], "kapali modda gonder callback YASAK"
        assert aralar == []
        # Hiçbir durum/yan etki yazılmamalı:
        row = conn.execute("SELECT gonderim_durumu, son_gonderim_tarihi, deneme_sayisi, "
                           "kiralama_zamani FROM esnaflar WHERE id=?", (id1,)).fetchone()
        assert row["gonderim_durumu"] == m.HAZIR
        assert row["son_gonderim_tarihi"] is None and row["kiralama_zamani"] is None
        assert row["deneme_sayisi"] == 0
        assert conn.execute("SELECT COUNT(*) FROM mesajlar").fetchone()[0] == 0
    finally:
        conn.close(); os.unlink(yol)


def test_izin_ve_eksik_veri_elenir_ve_gerekcesi_bilinir():
    conn, yol = _veritabani()
    try:
        izinsiz = _kayit_ekle(conn, isletme="Izinsiz")
        adresiz = _kayit_ekle(conn, isletme="Adresiz", telefon="905300000001", adres="")
        telbos = _kayit_ekle(conn, isletme="Telbos", telefon="", kod="TRM-TEL-BOS")
        tam = _kayit_ekle(conn, isletme="Tam", telefon="905300000002")
        m.sema_goc_uygula(conn)
        for esnaf_id in (izinsiz, adresiz, telbos, tam):
            conn.execute("UPDATE esnaflar SET izin = 1 WHERE id = ?", (esnaf_id,))
        conn.commit()
        conn.execute("UPDATE esnaflar SET izin = 0 WHERE id = ?", (izinsiz,))
        conn.commit()
        adaylar = m.uygun_esnaflar(conn, _yapi(), TUR, 20)
        assert [a["id"] for a in adaylar] == [tam], "yalnizca izin+adres+telefon tam olan secilir"
        elenen = {e["id"]: e["gerekce"] for e in m.engelli_kayitlar(conn, _yapi())}
        assert elenen[izinsiz] == "izin-yok"
        assert adresiz in elenen and elenen[adresiz].startswith("adres-bos")
        assert telbos in elenen and elenen[telbos] == "telefon-bos"
    finally:
        conn.close(); os.unlink(yol)


def test_acik_mod_gonderir_ve_durumu_gunceller():
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn, isletme="Canli Dukkan")
        m.sema_goc_uygula(conn)
        conn.execute("UPDATE esnaflar SET izin = 1 WHERE id = ?", (id1,))
        conn.commit()
        denenmis, aralar = [], []
        motor = _motor(conn, _yapi(OTONOM_GONDERIM="1"), kayitlar=denenmis, aralar=aralar)
        sonuc = motor.bir_tur()
        assert sonuc["gonderilen"] == 1 and denenmis == [id1]
        row = conn.execute("SELECT gonderim_durumu, son_gonderim_tarihi, gonderim_sayisi, "
                           "deneme_sayisi, kiralama_zamani FROM esnaflar WHERE id=?", (id1,)).fetchone()
        assert row["gonderim_durumu"] == m.GONDERILDI
        assert row["son_gonderim_tarihi"].startswith("2026-10-19")
        assert row["gonderim_sayisi"] == 1 and row["deneme_sayisi"] == 0
        assert row["kiralama_zamani"] is None, "basarili gonderimde kiralama birakilmali"
        # Motor kendi basina mesajlar tablosuna YAZMAZ (bu, teslim-onayli
        # _esnaf_tanitimi_gonder'in sozlesmesidir).
        assert conn.execute("SELECT COUNT(*) FROM mesajlar").fetchone()[0] == 0
        assert conn.execute("SELECT deger FROM otonom_durum WHERE anahtar='ilk_gonderim_gunu'").fetchone()[0] == "2026-10-19"
    finally:
        conn.close(); os.unlink(yol)


def test_teslim_edilmeyen_mesaj_hata_sayacina_yazilir():
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn)
        m.sema_goc_uygula(conn)
        conn.execute("UPDATE esnaflar SET izin = 1 WHERE id = ?", (id1,))
        conn.commit()

        def basarisiz(esnaf_id):
            return {"status": "gonderilemedi", "mesaj": "alici dogrulanamadi"}

        motor = _motor(conn, _yapi(OTONOM_GONDERIM="1"), gonder=basarisiz)
        sonuc = motor.bir_tur()
        assert sonuc["gonderilen"] == 0
        row = conn.execute("SELECT gonderim_durumu, deneme_sayisi, son_hata FROM esnaflar WHERE id=?",
                           (id1,)).fetchone()
        assert row["gonderim_durumu"] == m.HATA and row["deneme_sayisi"] == 1
        assert row["son_hata"] == "alici dogrulanamadi"
        assert conn.execute("SELECT COUNT(*) FROM mesajlar").fetchone()[0] == 0
        # Azami deneme asilana kadar hata kaydi yeniden siraya girer:
        assert [a["id"] for a in m.uygun_esnaflar(conn, _yapi(OTONOM_AZ_DENEME=3), TUR, 20)] == [id1]
        conn.execute("UPDATE esnaflar SET deneme_sayisi = 3 WHERE id = ?", (id1,))
        conn.commit()
        assert m.uygun_esnaflar(conn, _yapi(OTONOM_AZ_DENEME=3), TUR, 20) == []
    finally:
        conn.close(); os.unlink(yol)


def test_hat_basi_cooldown():
    conn, yol = _veritabani()
    try:
        az_once = _kayit_ekle(conn, telefon="905300000010")
        fazla_once = _kayit_ekle(conn, telefon="905300000011")
        m.sema_goc_uygula(conn)
        for esnaf_id, saat_once in ((az_once, 1), (fazla_once, 25)):
            conn.execute(
                "UPDATE esnaflar SET izin = 1, gonderim_durumu = ?, son_gonderim_tarihi = ? "
                "WHERE id = ?",
                (m.GONDERILDI,
                 (TUR - timedelta(hours=saat_once)).strftime("%Y-%m-%d %H:%M:%S"), esnaf_id),
            )
        conn.commit()
        adaylar = m.uygun_esnaflar(conn, _yapi(OTONOM_COOLDOWN_SART=24), TUR, 20)
        assert [a["id"] for a in adaylar] == [fazla_once], \
            "24 saat dolmayan hat tekrar siraya giremez"
    finally:
        conn.close(); os.unlink(yol)


def test_gunluk_tavan_isinma_egrisi():
    conn, yol = _veritabani()
    try:
        yapi = _yapi(OTONOM_GUNLUK_LIMIT=5, OTONOM_ISINMA_ADIM=2, OTONOM_ISINMA_TAVAN=20)
        m.sema_goc_uygula(conn)
        assert m.gunluk_tavan(yapi, conn, TUR) == 5, "henuz hic gonderim yokken ilk gun tavanı"
        m._durum_yazisi(conn, "ilk_gonderim_gunu", "2026-10-16")
        assert m.gunluk_tavan(yapi, conn, TUR) == 11, "3 gun gecti: 5 + 2*3"
        m._durum_yazisi(conn, "ilk_gonderim_gunu", "2026-01-01")
        assert m.gunluk_tavan(yapi, conn, TUR) == 20, "tavan asilamaz"
    finally:
        conn.close(); os.unlink(yol)


def test_gunluk_tavan_dolunca_hicbir_sey_gonderilmez():
    conn, yol = _veritabani()
    try:
        m.sema_goc_uygula(conn)
        bugun = TUR.strftime("%Y-%m-%d %H:%M:%S")
        for i in range(5):
            esnaf_id = _kayit_ekle(conn, telefon=f"9053000001{i}")
            conn.execute("UPDATE esnaflar SET izin=1, gonderim_durumu=?, son_gonderim_tarihi=? "
                         "WHERE id=?", (m.GONDERILDI, bugun, esnaf_id))
        aday = _kayit_ekle(conn, telefon="905300000200")
        conn.execute("UPDATE esnaflar SET izin=1 WHERE id=?", (aday,))
        conn.commit()
        denenmis = []
        motor = _motor(conn, _yapi(OTONOM_GONDERIM="1"), kayitlar=denenmis)
        sonuc = motor.bir_tur()
        assert sonuc["sebep"] == "tavan" and denenmis == []
        assert m.bugunku_gonderilen(conn, TUR) == 5
    finally:
        conn.close(); os.unlink(yol)


def test_kiralama_cift_gonderimi_ve_bayat_kiralamiyi_engeller():
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn)
        m.sema_goc_uygula(conn)
        motor = _motor(conn, _yapi(OTONOM_GONDERIM="1"))
        assert motor._kiralama(conn, id1, TUR) is True
        assert motor._kiralama(conn, id1, TUR) is False, "ayni satir ikinci kez kiralanamaz"
        # Taze kiralama bayat sayilmaz:
        assert m.bayat_kiralama_temizle(conn, TUR, 30) == 0
        # 31 dakika eskiye cekilince cozulur ve hata sayaci yukselir:
        eskiye = (TUR - timedelta(minutes=31)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("UPDATE esnaflar SET kiralama_zamani = ? WHERE id = ?", (eskiye, id1))
        conn.commit()
        assert m.bayat_kiralama_temizle(conn, TUR, 30) == 1
        row = conn.execute("SELECT gonderim_durumu, deneme_sayisi, son_hata FROM esnaflar WHERE id=?",
                           (id1,)).fetchone()
        assert row["gonderim_durumu"] == m.HATA and row["deneme_sayisi"] == 1
        assert "bayat-kiralama" in row["son_hata"]
    finally:
        conn.close(); os.unlink(yol)


def test_oturum_hazir_degilse_gonderim_yok():
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn)
        m.sema_goc_uygula(conn)
        conn.execute("UPDATE esnaflar SET izin=1 WHERE id=?", (id1,))
        conn.commit()
        denenmis = []
        motor = _motor(conn, _yapi(OTONOM_GONDERIM="1"), kayitlar=denenmis, oturum=False)
        assert motor.bir_tur()["sebep"] == "oturum" and denenmis == []
    finally:
        conn.close(); os.unlink(yol)


def test_is_saatleri_penceresi_istanbul_saatiyle():
    conn, yol = _veritabani()
    try:
        yapi = _yapi(OTONOM_SAAT_PENCERESI="09:00-19:00", OTONOM_SAAT_DILIMI="Europe/Istanbul")
        # Saat dilimi bagimliligi olmayan davranislar her kosumda dogrulanir:
        acik, nede = m.pencere_ici_mi(yapi, datetime(2026, 10, 19, 3, 0))
        assert acik is True and "saat-dilimi-yok" in nede, "naive zaman -> pencere acilir + loglanir"
        bos, neden = m.pencere_ici_mi(_yapi(OTONOM_SAAT_PENCERESI="bozuk"), TUR)
        assert bos is True and "gecersiz" in neden
        # tzdata varsa gercek pencere mantigi denenir (Windows'ta bulunmayabilir):
        icinde, kaynak = m.pencere_ici_mi(yapi, TUR)
        if kaynak == "saat-dilimi-yok-lokal":
            print("   (zoneinfo/Europe-Istanbul yok -> pencere mantigi atlandi)")
            return
        assert icinde is True, f"12:00 UTC = 15:00 TR, pencere icinde olmali ({kaynak})"
        gece = datetime(2026, 10, 19, 22, 0, tzinfo=timezone.utc)  # 01:00 TR
        assert m.pencere_ici_mi(yapi, gece)[0] is False
        asan = _yapi(OTONOM_SAAT_PENCERESI="22:00-06:00", OTONOM_SAAT_DILIMI="Europe/Istanbul")
        # 18:00 UTC = 21:00 TR -> 22:00-06:00 disinda
        assert m.pencere_ici_mi(asan, datetime(2026, 10, 19, 18, 0, tzinfo=timezone.utc))[0] is False
        # 21:00 UTC = 00:00 TR -> gece yarisini asan pencerenin ICINDE
        assert m.pencere_ici_mi(asan, datetime(2026, 10, 19, 21, 0, tzinfo=timezone.utc))[0] is True
    finally:
        conn.close(); os.unlink(yol)


def test_rastgele_ara_varsayilan_45_90():
    motor = _motor(sqlite3.connect(":memory:"), _yapi())
    for _ in range(200):
        assert 45 <= motor._varsayilan_ara() <= 90


def test_ara_mesaji_gonderimler_arasinda_ve_ilk_gonderimden_once_yok():
    conn, yol = _veritabani()
    try:
        m.sema_goc_uygula(conn)
        for i in range(3):
            esnaf_id = _kayit_ekle(conn, telefon=f"90530000030{i}")
            conn.execute("UPDATE esnaflar SET izin=1 WHERE id=?", (esnaf_id,))
        conn.commit()
        aralar, denenmis = [], []
        motor = _motor(conn, _yapi(OTONOM_GONDERIM="1", OTONOM_MIN_ARA_SN=45,
                                   OTONOM_MAX_ARA_SN=90), kayitlar=denenmis, aralar=aralar)
        motor.rastgele_ara = lambda: 47
        sonuc = motor.bir_tur()
        assert len(denenmis) == 3
        # 3 gonderim -> 2 ara (son gonderimden sonra bosuna bekleme yok)
        assert aralar == [47, 47], f"beklendi [47,47], bulundu {aralar}"
        assert sonuc["gonderilen"] == 3
    finally:
        conn.close(); os.unlink(yol)


def test_gelen_mesaj_kaydi_tekilleme_ve_opt_out():
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn)
        m.sema_goc_uygula(conn)
        conn.execute("UPDATE esnaflar SET izin=1 WHERE id=?", (id1,))
        conn.commit()

        def mesaj_kaydet(c, esnaf_id, gonderen, metin):
            c.execute("INSERT INTO mesajlar (esnaf_id, gonderen, mesaj) VALUES (?,?,?)",
                      (esnaf_id, gonderen, metin))
            c.commit()

        imza1 = m.imza("Test Dukkan", "Ucreti ne kadar?")
        sonuc = m.gelen_mesaj_kaydet(conn, id1, "Ucreti ne kadar?", imza1, mesaj_kaydet, simdi=TUR)
        assert sonuc["kaydedildi"] is True and sonuc["opt_out"] is False
        assert conn.execute("SELECT COUNT(*) FROM mesajlar WHERE gonderen='ESNAF'").fetchone()[0] == 1
        assert conn.execute("SELECT gelen_yanit FROM esnaflar WHERE id=?", (id1,)).fetchone()[0] == "Ucreti ne kadar?"
        # Ayni mesaj tekrar islenmez:
        tekrar = m.gelen_mesaj_kaydet(conn, id1, "Ucreti ne kadar?", imza1, mesaj_kaydet, simdi=TUR)
        assert tekrar["yinelenen"] is True
        assert conn.execute("SELECT COUNT(*) FROM mesajlar").fetchone()[0] == 1
        # Opt-out: kalici olarak listeden cikar
        imza2 = m.imza("Test Dukkan", "DUR")
        opt = m.gelen_mesaj_kaydet(conn, id1, "DUR", imza2, mesaj_kaydet, simdi=TUR)
        assert opt["opt_out"] is True and opt["kara_liste"] is True
        row = conn.execute("SELECT opt_out, gonderim_durumu FROM esnaflar WHERE id=?", (id1,)).fetchone()
        assert row["opt_out"] == 1 and row["gonderim_durumu"] == m.OPT_CIKTI
        assert m.uygun_esnaflar(conn, _yapi(), TUR, 20) == []
        # Opt-out kelime testleri
        assert m.opt_out_mu("DUR") is True
        assert m.opt_out_mu("Durum nedir?") is False, "'durum' kelimesi opt-out sayilmamali"
        assert m.opt_out_mu("İPTAL") is True
        assert m.opt_out_mu("iptal ediyorum") is True
        assert m.opt_out_mu("Lütfen beni listeden çıkar") is True
        assert m.opt_out_mu("Mesaj atma artık") is True
        assert m.opt_out_mu("Reklam bitti mi, ücret ne kadar?") is False
        assert m.opt_out_mu("") is False
    finally:
        conn.close(); os.unlink(yol)


def test_kara_liste_numara_biciminden_bagimsiz_kalicidir():
    """Red, NUMARA ile kalıcıdır: kayıt silinip taramayla aynı numara yeni id ile
    geri gelse de, numara hangi biçimde yazılmış olursa olsun bir daha sıraya girmez."""
    conn, yol = _veritabani()
    try:
        m.sema_goc_uygula(conn)

        def mesaj_kaydet(c, esnaf_id, gonderen, metin):
            c.execute("INSERT INTO mesajlar (esnaf_id, gonderen, mesaj) VALUES (?,?,?)",
                      (esnaf_id, gonderen, metin))
            c.commit()

        # Panelden '0530 000 00 00' biçiminde gelen bir kayıt 'İPTAL' derse
        # kara liste kanonik 905300000000 ile dolmalı.
        id1 = _kayit_ekle(conn, telefon="0530 000 00 00")
        conn.execute("UPDATE esnaflar SET izin=1 WHERE id=?", (id1,))
        conn.commit()
        sonuc = m.gelen_mesaj_kaydet(conn, id1, "İPTAL", m.imza("Test Dukkan", "iptal"),
                                     mesaj_kaydet, simdi=TUR)
        assert sonuc["opt_out"] is True and sonuc["kara_liste"] is True
        kara = [r["telefon"] for r in conn.execute("SELECT telefon FROM kara_liste")]
        assert kara == ["905300000000"]
        for bicim in ("+90 530 000 00 00", "905300000000", "0530 000 00 00", "5300000000"):
            assert m.kara_listede_mi(conn, bicim) is True, bicim

        # Eski satır tamamen silinip tarama aynı numarayı yeni id ile geri yazsa
        # bile uygun_esnaflar onu asla seçmez.
        conn.execute("DELETE FROM esnaflar WHERE id=?", (id1,))
        conn.commit()
        id2 = _kayit_ekle(conn, telefon="+90 530 000 00 00")
        conn.execute("UPDATE esnaflar SET izin=1 WHERE id=?", (id2,))
        conn.commit()
        assert m.uygun_esnaflar(conn, _yapi(), TUR, 20) == []
        # Gönderim kapalı olsa da hedefleyici aynı elenmeyi görür: reddedilen
        # kayıt 'engel' gerekçesiyle raporlanır, sessizce kaybolmaz.
        assert m.engelli_kayitlar(conn, _yapi())[0]["gerekce"] == "kara-liste"

        # Kara listeden çıkarmak (panel işlemi) numaranın tüm biçimlerini tanır.
        conn.execute("DELETE FROM kara_liste WHERE telefon=?", ("905300000000",))
        conn.execute("UPDATE esnaflar SET opt_out=0, gonderim_durumu=? WHERE id=?",
                     (m.HAZIR, id2))
        conn.commit()
        assert [k["id"] for k in m.uygun_esnaflar(conn, _yapi(), TUR, 20)] == [id2]
    finally:
        conn.close(); os.unlink(yol)


def test_bilinen_esnaf_eleman_kuyrugu_dolu_iken_durur():
    """Tavan 5 ama aday 8 ise: bir turda en fazla 5 gonderim, kalan sirada kalir."""
    conn, yol = _veritabani()
    try:
        m.sema_goc_uygula(conn)
        for i in range(8):
            esnaf_id = _kayit_ekle(conn, telefon=f"9053000008{i}")
            conn.execute("UPDATE esnaflar SET izin=1 WHERE id=?", (esnaf_id,))
        conn.commit()
        denenmis = []
        motor = _motor(conn, _yapi(OTONOM_GONDERIM="1", OTONOM_GUNLUK_LIMIT=5),
                       kayitlar=denenmis)
        motor.rastgele_ara = lambda: 45
        sonuc = motor.bir_tur()
        assert len(denenmis) == 5 and sonuc["gonderilen"] == 5
        assert m.bugunku_gonderilen(conn, TUR) == 5
        # kalan 3 kayit hala sirada:
        assert [a["id"] for a in m.uygun_esnaflar(conn, _yapi(), TUR, 20)] and len(
            m.uygun_esnaflar(conn, _yapi(), TUR, 20)) == 3
    finally:
        conn.close(); os.unlink(yol)


# ---------------------------------------------------------------------------
# PANEL ONAYI (izin_ver) — operatörün tıkladığı tek kapı
# ---------------------------------------------------------------------------
def test_onay_kuyruga_alir_kapali_modda_bile_mesaj_gondermez():
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn, isletme="Onay Bekleyen")
        m.sema_goc_uygula(conn)
        assert m.uygun_esnaflar(conn, _yapi(), TUR, 20) == [], "onay öncesi sıra boş"

        sonuc = m.izin_ver(conn, id1, 1, simdi=TUR, kaynak="test-onay")
        assert sonuc["ok"] and sonuc["izin"] == 1 and sonuc["onceki"] == 0
        assert [a["id"] for a in m.uygun_esnaflar(conn, _yapi(), TUR, 20)] == [id1]
        denetim = conn.execute("SELECT izin, kaynak FROM izin_log WHERE esnaf_id=?",
                               (id1,)).fetchall()
        assert [(r["izin"], r["kaynak"]) for r in denetim] == [(1, "test-onay")], \
            "panel kararı denetim kaydı olmadan bırakılmamalı"

        # ONAY, MOTORU AÇMAZ: OTONOM_GONDERIM=0 iken onaylı kayıt yalnızca sıradadır.
        denenmis = []
        tur = _motor(yol, _yapi(OTONOM_GONDERIM="0"), kayitlar=denenmis).bir_tur()
        assert tur["mod"] == "kapali" and tur["gonderilen"] == 0 and denenmis == []
        assert conn.execute("SELECT gonderim_durumu FROM esnaflar WHERE id=?",
                            (id1,)).fetchone()["gonderim_durumu"] == m.HAZIR
    finally:
        conn.close(); os.unlink(yol)


def test_onay_acik_motorda_tek_mesaj_gonderir():
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn, isletme="Onayli")
        m.sema_goc_uygula(conn)
        m.izin_ver(conn, id1, 1, simdi=TUR)
        denenmis = []
        tur = _motor(yol, _yapi(OTONOM_GONDERIM="1"), kayitlar=denenmis).bir_tur()
        assert tur["gonderilen"] == 1 and denenmis == [id1]
    finally:
        conn.close(); os.unlink(yol)


def test_kara_listedeki_numara_panel_onayini_ezemez():
    """'DUR' demiş bir kişi, operatörün ONAY tuşuyla yeniden mesaj alamaz.

    Red numara ile bağlıdır: satır silinip taramayla yeni id olarak geri gelse
    bile, ve kara liste farklı numara biçimiyle yazılmış olsa da geçer.
    """
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn, isletme="Reddeden", telefon="905300000000")
        m.sema_goc_uygula(conn)
        m.kara_listeye_ekle(conn, "0530 000 00 00", "DUR yazdi", simdi=TUR)

        sonuc = m.izin_ver(conn, id1, 1, simdi=TUR, kaynak="test-onay")
        assert sonuc == {"ok": False, "sebep": "kara-liste", "esnaf_id": id1}
        assert conn.execute("SELECT izin FROM esnaflar WHERE id=?",
                            (id1,)).fetchone()["izin"] == 0
        assert m.uygun_esnaflar(conn, _yapi(), TUR, 20) == []
        red = conn.execute("SELECT kaynak FROM izin_log WHERE esnaf_id=?",
                           (id1,)).fetchone()["kaynak"]
        assert red.endswith("#red:kara-liste"), "reddedilen onay da iz bırakmalı"
    finally:
        conn.close(); os.unlink(yol)


def test_opt_out_ve_telefonsuz_kayit_onaylanamaz():
    conn, yol = _veritabani()
    try:
        opt = _kayit_ekle(conn, isletme="Opt Out", telefon="905300000009")
        telsiz = _kayit_ekle(conn, isletme="Telsiz", telefon="", kod="TRM-IZSIZ")
        m.sema_goc_uygula(conn)
        conn.execute("UPDATE esnaflar SET opt_out = 1 WHERE id = ?", (opt,))
        conn.commit()
        assert m.izin_ver(conn, opt, 1, simdi=TUR)["sebep"] == "opt-out"
        assert m.izin_ver(conn, telsiz, 1, simdi=TUR)["sebep"] == "telefon-yok"
        assert m.izin_ver(conn, 999999, 1, simdi=TUR)["sebep"] == "kayit-yok"
        for esnaf_id in (opt, telsiz):
            assert conn.execute("SELECT izin FROM esnaflar WHERE id=?",
                                (esnaf_id,)).fetchone()["izin"] == 0
    finally:
        conn.close(); os.unlink(yol)


def test_adresi_bos_kayit_onaylanir_ama_motor_secmez():
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn, isletme="Adresiz", adres="")
        m.sema_goc_uygula(conn)
        sonuc = m.izin_ver(conn, id1, 1, simdi=TUR)
        assert sonuc["ok"] and sonuc["uyari"].startswith("adres-bos"), \
            "onay geçerli ama motor bu kaydı sıraya almaz - panel söylemeli"
        assert m.uygun_esnaflar(conn, _yapi(), TUR, 20) == []
    finally:
        conn.close(); os.unlink(yol)


def test_onay_geri_alinir_ve_sira_dusunur():
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn, isletme="Geri Alinan")
        m.sema_goc_uygula(conn)
        m.izin_ver(conn, id1, 1, simdi=TUR, kaynak="test-onay")
        assert len(m.uygun_esnaflar(conn, _yapi(), TUR, 20)) == 1
        geri = m.izin_ver(conn, id1, 0, simdi=TUR, kaynak="test-ret")
        assert geri["ok"] and geri["izin"] == 0 and geri["onceki"] == 1
        assert m.uygun_esnaflar(conn, _yapi(), TUR, 20) == []
        yazilan = conn.execute(
            "SELECT kaynak FROM izin_log WHERE esnaf_id=? ORDER BY rowid", (id1,)
        ).fetchall()
        assert [r["kaynak"] for r in yazilan] == ["test-onay", "test-ret"]
    finally:
        conn.close(); os.unlink(yol)


def test_cok_numarali_alanda_cep_redri_de_satiri_engeller():
    """Tarama kaydı 'sabit;cep' taşırken cep'ten 'DUR' gelirse satır durur.

    Eski davranışta tüm alan tek dama haline getirildiği için red eşleşmezdi
    ve reddetmiş olan esnafa mesaj gitmeye devam ederdi.
    """
    conn, yol = _veritabani()
    try:
        alan = "0 (256) 612 99 65;0 (530) 912 99 65"
        id1 = _kayit_ekle(conn, isletme="Iki Hatli", telefon=alan, kod="TRM-IKI-HAT")
        m.sema_goc_uygula(conn)
        assert not m.kara_listede_mi(conn, alan)
        m.kara_listeye_ekle(conn, "0530 912 99 65", "DUR yazdi", simdi=TUR)
        assert m.kara_listede_mi(conn, alan), "cepten gelen red alanın içinde bulunmalı"

        sonuc = m.izin_ver(conn, id1, 1, simdi=TUR)
        assert sonuc["ok"] is False and sonuc["sebep"] == "kara-liste"
        conn.execute("UPDATE esnaflar SET izin = 1 WHERE id = ?", (id1,))
        conn.commit()
        assert m.uygun_esnaflar(conn, _yapi(), TUR, 20) == [], "redli satır sıraya giremez"
        elenen = {e["id"]: e["gerekce"] for e in m.engelli_kayitlar(conn, _yapi())}
        assert elenen[id1] == "kara-liste"
    finally:
        conn.close(); os.unlink(yol)


def test_bosluklu_tek_numara_kara_listeyle_eslesir():
    conn, yol = _veritabani()
    try:
        id1 = _kayit_ekle(conn, isletme="Bosluklu", telefon="0530 000 00 00",
                          kod="TRM-BOSLUKLU")
        m.sema_goc_uygula(conn)
        m.kara_listeye_ekle(conn, "905300000000", "opt-out", simdi=TUR)
        assert m.kara_listede_mi(conn, "0530 000 00 00"), \
            "boşluk parçalaması numarayı kaybetmemeli"
        assert m.izin_ver(conn, id1, 1, simdi=TUR)["sebep"] == "kara-liste"
    finally:
        conn.close(); os.unlink(yol)


def test_sabit_hat_onayinda_panel_uyarisi_ve_mobil_alani():
    conn, yol = _veritabani()
    try:
        sabit = _kayit_ekle(conn, isletme="Sabit Hat", telefon="+90 256 612 48 60",
                            kod="TRM-SABIT")
        cep = _kayit_ekle(conn, isletme="Cep Hat", telefon="+90 530 912 99 65",
                          kod="TRM-CEP")
        m.sema_goc_uygula(conn)
        s = m.izin_ver(conn, sabit, 1, simdi=TUR)
        assert s["ok"] and s["mobil"] == "" and "mobil-degil" in s["uyari"]
        c = m.izin_ver(conn, cep, 1, simdi=TUR)
        assert c["ok"] and c["mobil"] == "905309129965" and "uyari" not in c
    finally:
        conn.close(); os.unlink(yol)


def _tumu_calistir():
    testler = [(ad, f) for ad, f in sorted(globals().items())
               if ad.startswith("test_") and callable(f)]
    basarisiz = 0
    for ad, islev in testler:
        try:
            islev()
            print(f"  OK   {ad}")
        except Exception as hata:
            basarisiz += 1
            print(f"  HATA {ad}: {type(hata).__name__}: {hata}")
    print(f"\n{len(testler) - basarisiz}/{len(testler)} gecti")
    return 1 if basarisiz else 0


if __name__ == "__main__":
    raise SystemExit(_tumu_calistir())
