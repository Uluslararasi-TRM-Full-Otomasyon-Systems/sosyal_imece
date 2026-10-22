# -*- coding: utf-8 -*-
"""TRM otonom gönderim motoru (Selenium'dan bağımsız, saf mantık).

api_server_2.py import edilir edilmez Chrome + WhatsApp oturumu başlattığı için
bu modülde hiçbir Selenium/oturum bağımlılığı YOKTUR: motor, gönderme ve
oturum-yoklama işlevleri CALLBACK olarak dışarıdan verilir. Böylece döngünün
tamamı (uygunluk, cooldown, günlük tavan, kapalı-mod güvenliği) geçici bir
SQLite dosyası üzerinde test edilebilir.

Güvenlik varsayımları (hepsi fail-closed):
  * OTONOM_GONDERIM=0 -> motor HİÇBİR şeye dokunmaz: ne gönderir, ne de
    veritabanına durum yazar. Yalnızca "kim sıradaydı" raporunu loglar.
  * esnaflar.izin=0 -> kayıt gönderilemez sayılır. Toplu tanıtım için ön izin
    verisi zorunlu; listede izin yoksa motor o kaydı asla seçmez.
  * adres boşsa şablon kilidi (esnaf_sablonu) zaten patlar; motor o kaydı
    denemeden önce eler ki boşuna hat/açıktan sohbet üretmesin.
"""

import os
import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python 3.8
    ZoneInfo = None

GONDERIM_KAPALI_METNI = "KAPALI (OTONOM_GONDERIM=0)"

# esnaflar.gonderim_durumu değer kümesi (YENI alan; eski `durum` alanının
# 'onayli'/'GÖNDERİLDİ' anlamlarına dokunulmaz).
HAZIR = "gonderime_hazir"
ISLENMEKTE = "gonderiliyor"
GONDERILDI = "gonderildi"
HATA = "hata"
OPT_CIKTI = "opt_out"

_GOC_KOLONLARI = (
    ("izin", "INTEGER DEFAULT 0"),
    ("gonderim_durumu", f"TEXT DEFAULT '{HAZIR}'"),
    ("son_gonderim_tarihi", "DATETIME"),
    ("gonderim_sayisi", "INTEGER DEFAULT 0"),
    ("deneme_sayisi", "INTEGER DEFAULT 0"),
    ("son_hata", "TEXT"),
    ("opt_out", "INTEGER DEFAULT 0"),
    ("opt_out_tarihi", "DATETIME"),
    ("son_gelen_imza", "TEXT"),
    # Kiralama zaman damgası: süreç gönderim ortasında ölürse satır
    # 'gonderiliyor' durumunda takılı kalır; bayat kiralama temizliği bunu
    # çözüp kaydı yeniden sıraya alır.
    ("kiralama_zamani", "DATETIME"),
    # Canlı şemada zaten var; eski/boş bir DB üzerinde de motorun gelen mesaj
    # yazısı patlamasın diye göç listesinde tutulur (ALTER idempotenttir).
    ("gelen_yanit", "TEXT"),
    # Hiper-yerel filtre: YALNIZCA dış kaynaktan (OSM etiketleri) okunduğu gibi
    # yazılır, asla tahmin edilmez. Panel mahalle/ilçe göre burada süzer.
    ("ilce", "TEXT"),
    ("mahalle", "TEXT"),
    ("enlem", "REAL"),
    ("boylam", "REAL"),
    # ODbL atfı için kaynak imzası (OSM:node/123 ya da liste:dosya.csv#4).
    ("kaynak", "TEXT"),
)


# ---------------------------------------------------------------------------
# YAPILANDIRMA
# ---------------------------------------------------------------------------
def _bayrak(deger, varsayilan=False):
    if deger is None:
        return varsayilan
    return str(deger).strip().lower() in ("1", "true", "evet", "on", "open", "acik")


def _sayic(deger, varsayilan):
    try:
        return int(str(deger).strip())
    except (TypeError, ValueError):
        return varsayilan


class Yapilandirma:
    """Ortam değişkenlerinden okunan gönderim politikası."""

    def __init__(self, environ=None):
        e = os.environ if environ is None else environ
        self.gonderim_acik = _bayrak(e.get("OTONOM_GONDERIM"), False)
        self.toplu_sayi = max(1, _sayic(e.get("OTONOM_TOPLU_SAYI"), 20))
        self.gunluk_limit = max(1, _sayic(e.get("OTONOM_GUNLUK_LIMIT"), 5))
        self.isinma_adim = max(0, _sayic(e.get("OTONOM_ISINMA_ADIM"), 2))
        self.isinma_tavan = max(self.gunluk_limit, _sayic(e.get("OTONOM_ISINMA_TAVAN"), 20))
        self.min_ara = max(1, _sayic(e.get("OTONOM_MIN_ARA_SN"), 45))
        self.max_ara = max(self.min_ara, _sayic(e.get("OTONOM_MAX_ARA_SN"), 90))
        self.basina_cooldown_saat = max(1, _sayic(e.get("OTONOM_COOLDOWN_SART"), 24))
        self.az_deneme = max(1, _sayic(e.get("OTONOM_AZ_DENEME"), 3))
        self.kiralama_yas_dn = max(5, _sayic(e.get("OTONOM_KIRALAMA_YAS_DK"), 30))
        self.yoklama_sn = max(5, _sayic(e.get("OTONOM_YOKLAMA_SN"), 60))
        self.saat_penceresi = str(e.get("OTONOM_SAAT_PENCERESI") or "09:00-19:00").strip()
        self.saat_dilimi = str(e.get("OTONOM_SAAT_DILIMI") or "Europe/Istanbul").strip()
        self.otomatik_yanit_acik = _bayrak(e.get("OTONOM_OTOMATIK_YANIT"), False)
        self.gelen_mesaj_acik = _bayrak(e.get("OTONOM_GELEN_MESAJ"), True)
        self.gelen_yoklama_sn = max(15, _sayic(e.get("OTONOM_GELEN_YOKLAMA_SN"), 120))
        self.gelen_azami_sohbet = max(1, _sayic(e.get("OTONOM_GELEN_AZAMI_SOHBET"), 5))

    def sozler(self):
        return (
            f"gonderim={'ACIK' if self.gonderim_acik else GONDERIM_KAPALI_METNI}, "
            f"gunluk_tavan={self.gunluk_limit}+isinma(->{self.isinma_tavan}), "
            f"ara={self.min_ara}-{self.max_ara}sn, cooldown={self.basina_cooldown_saat}sa, "
            f"pencere={self.saat_penceresi}/{self.saat_dilimi}, "
            f"oto_yanit={'ACIK' if self.otomatik_yanit_acik else 'KAPALI'}"
        )


# ---------------------------------------------------------------------------
# SEHEMA GÖCÜ (idempotent)
# ---------------------------------------------------------------------------
def mevcut_kolonlar(conn, tablo="esnaflar"):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({tablo})")}


def sema_goc_uygula(conn):
    """Eklentili ALTER TABLE; tekrar tekrar çalıştırılabilir. Var olan veriye dokunmaz."""
    kolonlar = mevcut_kolonlar(conn)
    eklenen = []
    for ad, tanim in _GOC_KOLONLARI:
        if ad not in kolonlar:
            conn.execute(f"ALTER TABLE esnaflar ADD COLUMN {ad} {tanim}")
            eklenen.append(ad)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS otonom_durum ("
        "anahtar TEXT PRIMARY KEY, deger TEXT NOT NULL)"
    )
    # Kalıcı kara liste NUMARA ile tutulur: esnaf satırı silinip taramayla aynı
    # numara yeni id ile geri gelse bile red kalıcı kalsın.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS kara_liste ("
        "telefon TEXT PRIMARY KEY, gerekce TEXT NOT NULL, "
        "tarih DATETIME NOT NULL, kaynak TEXT)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_esnaf_otonom_uygun "
        "ON esnaflar(izin, opt_out, gonderim_durumu)"
    )
    # Operatörün panelde "izin ver"e bastığı an. Bu tablonun boş olması,
    # Canlıda izinli görünen satırların nereden geldiğini açıklanamaz kılar.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS izin_log ("
        "esnaf_id INTEGER NOT NULL, izin INTEGER NOT NULL, kaynak TEXT, "
        "zaman DATETIME NOT NULL)"
    )
    conn.commit()
    return eklenen


def _durum_okusu(conn, anahtar):
    row = conn.execute("SELECT deger FROM otonom_durum WHERE anahtar = ?", (anahtar,)).fetchone()
    return row[0] if row else None


def _durum_yazisi(conn, anahtar, deger):
    conn.execute(
        "INSERT INTO otonom_durum (anahtar, deger) VALUES (?, ?) "
        "ON CONFLICT(anahtar) DO UPDATE SET deger = excluded.deger",
        (anahtar, str(deger)),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# ZAMAN / PENCERE
# ---------------------------------------------------------------------------
def _saat_cevir(ddmm):
    saat, dakika = ddmm.split(":")
    return int(saat), int(dakika)


def pencere_ici_mi(yapi, simdi):
    """Verilen an iş saatleri penceresi içinde mi?

    VPS'in sistemi UTC; hedef kitle Türkiye. Pencere bu yüzden SAAT_DILIMI ile
    adlandırılır (varsayılan Europe/Istanbul). Verilen an naive (saat dilimsiz)
    ise ya da zoneinfo bulunamazsa pencere günün her saatine açılır ve çağıran
    taraf kararı hangi kaynakla verdiğini loglar - yanlış saat diliminde sessizce
    göndermemek için.
    """
    try:
        baslangic, bitis = yapi.saat_penceresi.split("-")
        bs, bd = _saat_cevir(baslangic.strip())
        es, ed = _saat_cevir(bitis.strip())
    except (ValueError, AttributeError):
        return True, "gecersiz-pencere-tum-gun"
    yerel = _yerel_saate_cevir(simdi, yapi.saat_dilimi)
    if yerel is None:
        return True, "saat-dilimi-yok-lokal"
    dakika_karsiligi = yerel.hour * 60 + yerel.minute
    acilis, kapanis = bs * 60 + bd, es * 60 + ed
    if acilis <= kapanis:
        icinde = acilis <= dakika_karsiligi < kapanis
    else:  # gece yarısını geçen pencere
        icinde = dakika_karsiligi >= acilis or dakika_karsiligi < kapanis
    return icinde, yerel.tzname()


def _yerel_saate_cevir(simdi, saat_dilimi):
    if ZoneInfo is None or simdi.tzinfo is None:
        return None
    try:
        return simdi.astimezone(ZoneInfo(saat_dilimi))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# GÖNDERİM POLİTİKASI
# ---------------------------------------------------------------------------
def gunluk_tavan(yapi, conn, simdi):
    """Isınma eğrisi: ilk gönderilen günden itibaren günde +adim, tavana kadar."""
    ilk = _durum_okusu(conn, "ilk_gonderim_gunu")
    if not ilk:
        return yapi.gunluk_limit
    try:
        ilk_tarih = datetime.strptime(str(ilk)[:10], "%Y-%m-%d").date()
    except ValueError:
        return yapi.gunluk_limit
    gecken_gun = max(0, (simdi.date() - ilk_tarih).days)
    return min(yapi.isinma_tavan, yapi.gunluk_limit + yapi.isinma_adim * gecken_gun)


def bugunku_gonderilen(conn, simdi):
    bugun = simdi.strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT COUNT(*) FROM esnaflar "
        "WHERE gonderim_durumu = ? AND substr(son_gonderim_tarihi, 1, 10) = ?",
        (GONDERILDI, bugun),
    ).fetchone()
    return int(row[0])


def bayat_kiralama_temizle(conn, simdi, yas_dk):
    """'gonderiliyor' durumunda ama kiralama damgası çok eski olan satırları
    çözer (örnek: gönderim ortasında süreç öldürüldü / reboot oldu). Serbest
    bırakılan satır hata sayacını da yükseltir ki sonsuz döngüye girmesin."""
    sinir = (simdi - timedelta(minutes=yas_dk)).strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "UPDATE esnaflar SET gonderim_durumu = ?, deneme_sayisi = "
        "COALESCE(deneme_sayisi, 0) + 1, son_hata = ?, kiralama_zamani = NULL "
        "WHERE COALESCE(gonderim_durumu, '') = ? AND COALESCE(kiralama_zamani, '0000') < ?",
        (HATA, f"bayat-kiralama ({yas_dk} dk asildi)", ISLENMEKTE, sinir),
    )
    conn.commit()
    return cur.rowcount


def uygun_esnaflar(conn, yapi, simdi, limit):
    """Sıraya girebilecek kayıtlar. Tüm elemeler fail-closed."""
    cooldown_siniri = (simdi - timedelta(hours=yapi.basina_cooldown_saat)).strftime("%Y-%m-%d %H:%M:%S")
    # red_edilmis(): telefon ALANINDAKİ her numarayı ayrı ayrı kara listeyle
    # karşılaştırır; 'sabit;cep' biçimli tarama kayıtlarında cepten gelen red
    # de satırı engellesin.
    kara_liste_fonksiyonu_kaydet(conn)
    rows = conn.execute(
        """
        SELECT id, isletme, telefon, adres, durum, gonderim_durumu,
               son_gonderim_tarihi, deneme_sayisi, opt_out, izin
        FROM esnaflar
        WHERE izin = 1
          AND COALESCE(opt_out, 0) = 0
          AND COALESCE(TRIM(telefon), '') <> ''
          AND COALESCE(TRIM(adres), '') <> ''
          AND COALESCE(TRIM(isletme), '') <> ''
          AND red_edilmis(COALESCE(telefon, '')) = 0
          AND COALESCE(deneme_sayisi, 0) < ?
          AND (
                gonderim_durumu IN (?, ?)
                OR (gonderim_durumu = ? AND
                    (son_gonderim_tarihi IS NULL OR son_gonderim_tarihi < ?))
              )
        ORDER BY COALESCE(son_gonderim_tarihi, '0000-01-01'), id
        LIMIT ?
        """,
        (yapi.az_deneme, HAZIR, HATA, GONDERILDI, cooldown_siniri, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def engelli_kayitlar(conn, yapi, limit=10):
    """Sırada olmak isteyip de politik/veri nedeniyle elenenler - teşhis için."""
    kara_liste_fonksiyonu_kaydet(conn)
    rows = conn.execute(
        """
        SELECT id, isletme,
               CASE
                 WHEN COALESCE(izin, 0) = 1 AND COALESCE(opt_out, 0) = 1 THEN 'opt_out'
                 WHEN red_edilmis(COALESCE(telefon, '')) = 1
                      THEN 'kara-liste'
                 WHEN COALESCE(izin, 0) = 0 THEN 'izin-yok'
                 WHEN COALESCE(TRIM(adres), '') = '' THEN 'adres-bos( sablon-kilitler)'
                 WHEN COALESCE(TRIM(telefon), '') = '' THEN 'telefon-bos'
                 WHEN COALESCE(deneme_sayisi, 0) >= ? THEN 'deneme-asildi'
                 ELSE 'cooldown'
               END AS gerekce
        FROM esnaflar
        WHERE COALESCE(opt_out, 0) = 0
          AND (red_edilmis(COALESCE(telefon, '')) = 1
               OR COALESCE(izin, 0) = 0
               OR COALESCE(TRIM(adres), '') = ''
               OR COALESCE(TRIM(telefon), '') = ''
               OR COALESCE(deneme_sayisi, 0) >= ?
               OR COALESCE(opt_out, 0) = 1)
        ORDER BY id LIMIT ?
        """,
        (yapi.az_deneme, yapi.az_deneme, limit),
    ).fetchall()
    return [{"id": r["id"], "isletme": r["isletme"], "gerekce": r["gerekce"]} for r in rows]


# ---------------------------------------------------------------------------
# METIN YARDIMCILARI (opt-out + gelen mesaj imzası)
# ---------------------------------------------------------------------------
_TR_DONUSUM = str.maketrans({
    # Türkçe harfler NFKD ile ASCII'ye AYRISMADIĞI için (é -> e+ ́ gibi değil),
    # [^a-z0-9] elemesi "çıkar"ı "c|kar" diye parçalardı. Elle eşliyoruz.
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "İ": "i",
    "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u",
    "â": "a", "Â": "a", "î": "i", "û": "u",
})


def _kelimeler(metin):
    cevrilmis = str(metin or "").translate(_TR_DONUSUM).lower()
    daginik = unicodedata.normalize("NFKD", cevrilmis)
    duz = "".join(c for c in daginik if not unicodedata.combining(c))
    return [w for w in re.split(r"[^a-z0-9]+", duz) if w]


OPT_OUT_KELIMELER = {
    # _kelimeler() şapka/noktalı harfleri düştüğü için hepsi ASCII yazılır.
    # Tek başına "dur" ticari-ileti reddinin standart anahtar kelimesidir; kelime
    # bazlı eşleşme sayesinde "durum" gibi sözcükleri yakalamaz.
    "dur", "durmak", "iptal", "istemiyorum", "istmiyorum", "kaydetme", "birak",
    "unsubscribe", "optout",
}
OPT_OUT_IFADELER = (
    "mesaj atma", "mesaj atmayin", "bana yazma", "listeden cikar",
    "abonelikten cik", "bir daha yazma", "reklam gonderme",
)


def opt_out_mu(metin):
    """'DUR' / 'listeden çıkar' gibi ticari-ileti reddi ifadelerini yakalar.

    Kelime bazlı eşleşme kullanılır: 'dur' kelimesi 'durum' içinde yanlışlıkla
    yakalanmamalı.
    """
    kelimeler = set(_kelimeler(metin))
    if kelimeler & OPT_OUT_KELIMELER:
        return True
    duz = " ".join(_kelimeler(metin))
    return any(ifade in duz for ifade in OPT_OUT_IFADELER)


def imza(kimlik, metin):
    """Aynı gelen mesajı iki kez işlememek için kısa imza."""
    return f"{_kelimeler(kimlik)[:3]}|{_kelimeler(metin)[:6]}"


# ---------------------------------------------------------------------------
# KARA LİSTE (numara bazlı, kalıcı)
# ---------------------------------------------------------------------------
def telefon_kanonik(deger):
    """'0530 000 00 00' / '+90 530 000 00 00' / '905300000000' -> 905300000000.

    Kara liste NUMARA ile tutulur; biçim farkı aynı kişiyi kurtarmamalı.
    """
    rakam = "".join(c for c in str(deger or "") if c.isdigit())
    if not rakam:
        return ""
    if rakam.startswith("0090"):
        rakam = rakam[4:]
    elif rakam.startswith("00"):
        return rakam  # yurt dışı numara:olduğu gibi kalır
    if rakam.startswith("0") and len(rakam) == 11:
        rakam = "9" + rakam
    elif rakam.startswith("5") and len(rakam) == 10:
        rakam = "90" + rakam
    return rakam


def kara_listeye_ekle(conn, telefon, gerekce, simdi=None, kaynak="opt-out"):
    kanonik = telefon_kanonik(telefon)
    if not kanonik:
        return False
    conn.execute(
        "INSERT INTO kara_liste (telefon, gerekce, tarih, kaynak) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(telefon) DO UPDATE SET gerekce = excluded.gerekce",
        (kanonik, str(gerekce)[:300],
         (simdi or datetime.now()).strftime("%Y-%m-%d %H:%M:%S"), kaynak),
    )
    conn.commit()
    return True


def numara_adyarlari(deger):
    """'0 (256) 612 99 65;0 (530) 912 99 65' -> ['02566129965', '905309129965'].

    Tarama kayıtlarının telefon alanı birden çok numara taşıyabiliyor. Yalnızca
    bütün alan dama yapılsa (rakamların birleşmesi) 'DUR' yazan mobil numara,
    alanın içinde ayrı bir numara olarak durduğu halde kara listeyle eşleşmez ve
    o esnafa yeniden mesaj giderdi. Yalnızca parçalara bölünse bu kez
    '0530 000 00 00' gibi boşluklu tek numara çöpe gider. İkisi de denenir.
    """
    ham = str(deger or "")
    adyarlar = [telefon_kanonik(ham)]
    for parca in re.split(r"[;,/|]+", ham):
        kanonik = telefon_kanonik(parca)
        if kanonik:
            adyarlar.append(kanonik)
    ciktilar = []
    for kanonik in adyarlar:
        if kanonik and kanonik not in ciktilar:
            ciktilar.append(kanonik)
    return ciktilar


def mobil_numara(telefon):
    """Alanın içindeki ilk cep numarası ('905309129965'), yoksa ''.

    Taramadan gelen kayıtların bir kısmı yalnızca sabit hat taşıyor; WhatsApp
    o numaraya gitmez. Onay bir kiralık günlük slot harcaması olduğu için
    panelde operatöre önceden söylenir.
    """
    for kanonik in numara_adyarlari(telefon):
        if len(kanonik) == 12 and kanonik.startswith("905"):
            return kanonik
    return ""


def kara_listede_mi(conn, telefon):
    """Alanın İÇİNDEKİ HERHANGİ bir numara reddedilmişse True (fail-closed)."""
    for kanonik in numara_adyarlari(telefon):
        if conn.execute("SELECT 1 FROM kara_liste WHERE telefon = ?", (kanonik,)).fetchone():
            return True
    return False


def kara_liste_fonksiyonu_kaydet(conn):
    """SQL'e red_edilmis(telefon) fonksiyonunu ekler; sorgular bunu çağırır."""
    conn.create_function(
        "red_edilmis", 1, lambda deger: 1 if kara_listede_mi(conn, deger) else 0
    )


# ---------------------------------------------------------------------------
# OPERATÖR ONAYI (esnaflar.izin)
# ---------------------------------------------------------------------------
def izin_ver(conn, esnaf_id, izin, simdi=None, kaynak="panel"):
    """Paneldeki ONAY/RET düğmesinin tek yazma yolu.

    Alıcının reddi her zaman operatörün onayından önce gelir: kara listedeki ya
    da opt_out işaretli bir numara ONAY'a basılsa da gönderilemez olur. Aksi
    halde "DUR" demiş bir kişi, operatörün bir tıkıyla yeniden mesaj alırdı.
    """
    satir = conn.execute(
        "SELECT id, telefon, adres, opt_out, COALESCE(izin, 0) AS izin FROM esnaflar "
        "WHERE id = ?", (int(esnaf_id),)
    ).fetchone()
    if satir is None:
        return {"ok": False, "sebep": "kayit-yok", "esnaf_id": esnaf_id}

    hedef = 1 if _bayrak(izin, False) else 0
    zaman = (simdi or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

    def _logla(yazilan_izin, ek_kaynak):
        conn.execute(
            "INSERT INTO izin_log (esnaf_id, izin, kaynak, zaman) VALUES (?, ?, ?, ?)",
            (int(esnaf_id), yazilan_izin, str(ek_kaynak)[:60], zaman),
        )

    if hedef == 0:
        conn.execute("UPDATE esnaflar SET izin = 0 WHERE id = ?", (int(esnaf_id),))
        _logla(0, kaynak)
        conn.commit()
        return {"ok": True, "esnaf_id": int(esnaf_id), "izin": 0,
                "onceki": int(satir["izin"])}

    telefon = str(satir["telefon"] or "").strip()
    if not telefon:
        _logla(1, f"{kaynak}#red:telefon-yok")
        conn.commit()
        return {"ok": False, "sebep": "telefon-yok", "esnaf_id": int(esnaf_id)}
    if kara_listede_mi(conn, telefon):
        _logla(1, f"{kaynak}#red:kara-liste")
        conn.commit()
        return {"ok": False, "sebep": "kara-liste", "esnaf_id": int(esnaf_id)}
    if int(satir["opt_out"] or 0) == 1:
        _logla(1, f"{kaynak}#red:opt-out")
        conn.commit()
        return {"ok": False, "sebep": "opt-out", "esnaf_id": int(esnaf_id)}

    conn.execute("UPDATE esnaflar SET izin = 1 WHERE id = ?", (int(esnaf_id),))
    _logla(1, kaynak)
    conn.commit()
    sonuc = {"ok": True, "esnaf_id": int(esnaf_id), "izin": 1,
             "onceki": int(satir["izin"]),
             "mobil": mobil_numara(satir["telefon"])}
    uyarilar = []
    if not str(satir["adres"] or "").strip():
        # Motor adresi boş kaydı sıraya almaz (şablon kilidi); onay tek başına
        # gönderim anlamına gelmez - panelde "adres bekleniyor" olarak görünür.
        uyarilar.append("adres-bos: motor bu kaydı sıraya almaz")
    if not sonuc["mobil"]:
        uyarilar.append("mobil-degil: WhatsApp sabit hattı açmaz, slot harcar")
    if uyarilar:
        sonuc["uyari"] = " · ".join(uyarilar)
    return sonuc


# ---------------------------------------------------------------------------
# GELEN MESAJI KAYDET (mesajlar + esnaflar.gelen_yanit + opt-out)
# ---------------------------------------------------------------------------
def gelen_mesaj_kaydet(conn, esnaf_id, gelen_metni, imza_degeri, mesaj_kaydet_fn, simdi=None):
    """Gelen mesajı kalıcı hale getirir. Opt-out ise kişiyi kalıcı olarak
    gönderim listesinden çıkarır. Dönen: yazilan/kaydedilen alanların özeti."""
    sonuc = {"kaydedildi": False, "opt_out": False, "yinelenen": False,
             "kara_liste": False}
    if esnaf_id is None:
        return sonuc
    row = conn.execute(
        "SELECT son_gelen_imza, telefon FROM esnaflar WHERE id = ?", (esnaf_id,)
    ).fetchone()
    if row is None:
        return sonuc
    if (row["son_gelen_imza"] or "") == imza_degeri:
        sonuc["yinelenen"] = True
        return sonuc
    conn.execute(
        "UPDATE esnaflar SET gelen_yanit = ?, son_gelen_imza = ? WHERE id = ?",
        (gelen_metni, imza_degeri, esnaf_id),
    )
    conn.commit()
    mesaj_kaydet_fn(conn, esnaf_id, "ESNAF", gelen_metni)
    sonuc["kaydedildi"] = True
    if opt_out_mu(gelen_metni):
        conn.execute(
            "UPDATE esnaflar SET opt_out = 1, opt_out_tarihi = ?, gonderim_durumu = ? "
            "WHERE id = ?",
            ((simdi or datetime.now()).strftime("%Y-%m-%d %H:%M:%S"), OPT_CIKTI, esnaf_id),
        )
        conn.commit()
        sonuc["opt_out"] = True
        # Numara da kalıcı kara listeye girer: kayıt silinip taramayla aynı
        # numara yeni id ile geri gelse bile bir daha mesaj gitmez.
        sonuc["kara_liste"] = kara_listeye_ekle(
            conn, row["telefon"], f"opt-out mesaji: {gelen_metni[:120]}", simdi
        )
    return sonuc


# ---------------------------------------------------------------------------
# MOTOR
# ---------------------------------------------------------------------------
class Motor:
    """Tek tur = bir kez yokla, politika uygula, gerekiyorsa gönder.

    Bağımlılıklar enjekte edilir (baglan, gonder, oturum_hazir, uyustur, simdi,
    rastgele_ara, log, mesaj_kaydet) ki testler Chrome başlatmadan çalışsın.
    """

    def __init__(self, yapi, baglan, gonder, oturum_hazir, uyustur, log,
                 simdi=None, rastgele_ara=None, mesaj_kaydet=None):
        self.yapi = yapi
        self.baglan = baglan
        self.gonder = gonder
        self.oturum_hazir = oturum_hazir
        self.uyustur = uyustur
        self.log = log
        self.simdi = simdi or (lambda: datetime.now().astimezone())
        self.rastgele_ara = rastgele_ara or self._varsayilan_ara
        self.mesaj_kaydet = mesaj_kaydet

    def _varsayilan_ara(self):
        import random
        return random.randint(self.yapi.min_ara, self.yapi.max_ara)

    # -- durum güncellemeleri ----------------------------------------------
    def _gonderildi_isaretle(self, conn, esnaf_id, simdi):
        conn.execute(
            "UPDATE esnaflar SET gonderim_durumu = ?, son_gonderim_tarihi = ?, "
            "gonderim_sayisi = COALESCE(gonderim_sayisi, 0) + 1, deneme_sayisi = 0, "
            "son_hata = NULL, kiralama_zamani = NULL WHERE id = ?",
            (GONDERILDI, simdi.strftime("%Y-%m-%d %H:%M:%S"), esnaf_id),
        )
        conn.commit()
        if not _durum_okusu(conn, "ilk_gonderim_gunu"):
            _durum_yazisi(conn, "ilk_gonderim_gunu", simdi.strftime("%Y-%m-%d"))

    def _hata_isaretle(self, conn, esnaf_id, gerekce):
        # Teslim edilmeyen gönderim mesajlar tablosuna YAZILMAZ (mevcut sözleşme).
        conn.execute(
            "UPDATE esnaflar SET gonderim_durumu = ?, deneme_sayisi = "
            "COALESCE(deneme_sayisi, 0) + 1, son_hata = ?, kiralama_zamani = NULL "
            "WHERE id = ?",
            (HATA, str(gerekce)[:400], esnaf_id),
        )
        conn.commit()

    def _kiralama(self, conn, esnaf_id, simdi):
        """Satırı atomik olarak 'gonderiliyor'a çevirir; eşzamanlı çift gönderimi
        ve (gönderim ortasında ölürsek) kendi kendimize kilitlenmeyi engeller."""
        cur = conn.execute(
            "UPDATE esnaflar SET gonderim_durumu = ?, kiralama_zamani = ? WHERE id = ? "
            "AND COALESCE(gonderim_durumu, '') <> ?",
            (ISLENMEKTE, simdi.strftime("%Y-%m-%d %H:%M:%S"), esnaf_id, ISLENMEKTE),
        )
        conn.commit()
        return cur.rowcount == 1

    # -- bir tur -------------------------------------------------------------
    def bir_tur(self):
        yapi = self.yapi
        simdi = self.simdi()
        conn = self.baglan()
        try:
            sema_goc_uygula(conn)
            adaylar = uygun_esnaflar(conn, yapi, simdi, yapi.toplu_sayi)
            engelliler = engelli_kayitlar(conn, yapi)
            tavan = gunluk_tavan(yapi, conn, simdi)
            yapilmis = bugunku_gonderilen(conn, simdi)

            if not yapi.gonderim_acik:
                # KAPALI mod: salt-okunur. Tek bir UPDATE/INSERT yazılmaz ve
                # Selenium tarafına hiç dokunulmaz (oturum yoklaması bile yapılmaz).
                self.log(
                    f"[OTONOM] {GONDERIM_KAPALI_METNI} | uygun kayit: {len(adaylar)} | "
                    f"bugunku {yapilmis}/{tavan} | aday id: "
                    f"{[a['id'] for a in adaylar] or '-'} | elenen: "
                    f"{[(e['id'], e['gerekce']) for e in engelliler] or '-'}"
                )
                return {"mod": "kapali", "aday": len(adaylar), "gonderilen": 0,
                        "aday_id": [a["id"] for a in adaylar], "elenen": engelliler,
                        "tavan": tavan, "bugunku": yapilmis}

            if not self.oturum_hazir():
                self.log("[OTONOM] Oturum hazir degil, bu atlandi (hicbir sey gonderilmedi).")
                return {"mod": "acik", "aday": len(adaylar), "gonderilen": 0, "sebep": "oturum"}

            pencere, kaynak = pencere_ici_mi(yapi, simdi)
            if not pencere:
                self.log(f"[OTONOM] Is saatleri disinda ({kaynak}), gonderim yok.")
                return {"mod": "acik", "aday": len(adaylar), "gonderilen": 0, "sebep": "pencere"}

            kalan = tavan - yapilmis
            if kalan <= 0:
                self.log(f"[OTONOM] Gunluk tavan doldu ({yapilmis}/{tavan}).")
                return {"mod": "acik", "aday": len(adaylar), "gonderilen": 0, "sebep": "tavan"}

            dondurulecek = []
            # Ölü süreçten kalan kiralamaları çöz, yoksa o kayıt sonsuza dek
            # 'gonderiliyor' etiketiyle sırada beklemez.
            cozulmus = bayat_kiralama_temizle(conn, simdi, yapi.kiralama_yas_dn)
            if cozulmus:
                self.log(f"[OTONOM] {cozulmus} bayat kiralama cozuldu (hata sayaci yukseltildi).")
            adaylar = uygun_esnaflar(conn, yapi, simdi, yapi.toplu_sayi)
            adaylar = adaylar[:kalan]
            for sira, aday in enumerate(adaylar):
                if not self._kiralama(conn, aday["id"], simdi):
                    self.log(f"[OTONOM] #{aday['id']} baska bir isleyicide, atlandi.")
                    continue
                self.log(
                    f"[OTONOM] Gonderiliyor #{aday['id']} "
                    f"{(aday['isletme'] or '')[:40]} | durum=ACIK"
                )
                govde = self.gonder(aday["id"]) or {}
                basarili = govde.get("status") == "basarili"
                if basarili:
                    self._gonderildi_isaretle(conn, aday["id"], simdi)
                    yapilmis += 1
                    dondurulecek.append(aday["id"])
                    self.log(f"[OTONOM] #{aday['id']} teslim edildi ve kayda gecti.")
                else:
                    gerekce = govde.get("mesaj") or govde.get("status") or "teslim onayi yok"
                    self._hata_isaretle(conn, aday["id"], gerekce)
                    self.log(f"[OTONOM] #{aday['id']} GONDERILEMEDI: {gerekce}")
                if sira < len(adaylar) - 1:
                    bekleme = self.rastgele_ara()
                    self.log(f"[OTONOM] {bekleme} sn ara (spam korumasi).")
                    self.uyustur(bekleme)
            return {"mod": "acik", "aday": len(adaylar), "gonderilen": len(dondurulecek),
                    "gonderilen_id": dondurulecek}
        finally:
            conn.close()

    def dongu(self):
        self.log(f"[OTONOM] Motor baslatildi | {self.yapi.sozler()}")
        while True:
            try:
                self.bir_tur()
            except Exception as hata:  # thread asla sessizce olmemeli
                self.log(f"[OTONOM HATA] {type(hata).__name__}: {hata}")
            self.uyustur(self.yapi.yoklama_sn)
