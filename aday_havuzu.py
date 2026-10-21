# -*- coding: utf-8 -*-
"""TRM aday havuzu — haritadan firma bul, esnaflar tablosuna ADAY olarak yaz.

BU MODÜL MESAJ GÖNDERMEZ. Tek işi: dış kaynaktan (OpenStreetMap veya operatörün
kendi listesi) firma adı/telefonu/adresi toplamak ve bunları `esnaflar`
tablosuna **izin=0, durum='ADAY'** ile yazmak. Gönderim motoru
(`otonom_motor.uygun_esnaflar`) yalnızca `izin = 1` satırları seçtiği için
buradan gelen hiçbir kayıt kendiliğinden sıraya giremez; rıza kararı operatörün
panel üzerinden vereceği ayrı bir işlemdir.

Neden OSM ve neden Google Maps değil: OSM verisi ODbL lisansıyla serbestçe
işlenebilir; Google Maps'i kazımak ise hem hizmet şartlarına aykırı hem de bu
sunucuda aynı Chrome profiliyle WhatsApp gönderimi yapan hattı riske atar.

Fail-closed kurallar:
  * isimsiz POI atlanır;
  * telefon kanonik biçimde kara listedeyse atlanır (red kalıcıdır);
  * MEVCUT bir satır asla geri dönüştürülmez: izin/opt_out/gonderim_durumu/
    durum alanlarına dokunulmaz (opt-out olmuş bir firma taramayla "yeni aday"
    olarak sıraya dönememeli);
  * `kod` UNIQUE olduğu için çakışan satır atlanır, overwrite edilmez.
"""

import csv
import hashlib
import json
import os
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

from otonom_motor import kara_listede_mi, sema_goc_uygula, telefon_kanonik

ADAY_DURUM = "ADAY"
OSM_LISANS = "ODbL 2.0 - aciklik: @OpenStreetMap katkicilari (https://www.openstreetmap.org/copyright)"
OZET_ANAHTAR = "aday_havuzu_ozet"

_VARSAYILAN_URL = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
# Kusadasi merkezi ~4x4 km. Genis kutu (13x17km) Overpass kuyrugunda 200sn'yi
# asiyor; ADAY_BBOX ile daraltarak büyütmek daha güvenilir.
_VARSAYILAN_BBOX = "37.845,27.245,37.885,27.285"
_SEKILLER = "shop|amenity@restaurant,cafe,bar,fast_food,pharmacy,bakery"


def _bayrak(deger, varsayilan=False):
    if deger is None:
        return varsayilan
    return str(deger).strip().lower() in ("1", "true", "evet", "on", "open", "acik")


def _sayic(deger, varsayilan):
    try:
        return int(str(deger).strip())
    except (TypeError, ValueError):
        return varsayilan


class AdayYapisi:
    def __init__(self, environ=None):
        e = os.environ if environ is None else environ
        self.tarama_acik = _bayrak(e.get("ADAY_TARAMA"), True)
        self.aralik_dk = max(10, _sayic(e.get("ADAY_ARALIK_DK"), 180))
        self.azami = max(1, _sayic(e.get("ADAY_AZAMI"), 300))
        self.bbox = str(e.get("ADAY_BBOX") or _VARSAYILAN_BBOX).strip()
        self.sekiller = str(e.get("ADAY_SEKILLER") or _SEKILLER).strip()
        self.url = [u.strip() for u in str(e.get("ADAY_OVERPASS_URL") or "").split(",") if u.strip()] or list(_VARSAYILAN_URL)
        # Overpass kuyruğu yavaş: Kuşadası merkez taraması ölçülen ~139 sn,
        # sunucu yüklüyken 180 sn'de bile doluyor. 3 saatte bir dönen bir arka
        # plan işi için 240 sn dinmek ucuz; erken kesmek havuzu boş bırakıyor.
        self.dinle_sn = max(30, _sayic(e.get("ADAY_CAGRI_SN"), 240))
        # Tüm aynalar boş/hata dönerse aralığı BEKLEMENİN anlamı yok: Overpass
        # yoğunluğu dakikalar içinde açılıyor, o yüzden kısa tekrarda dönüyor.
        self.tekrar_dk = max(1, _sayic(e.get("ADAY_TEKRAR_DK"), 10))

    def sozler(self):
        return (f"tarama={'ACIK' if self.tarama_acik else 'KAPALI'}, "
                f"aralik={self.aralik_dk}dk, tekrar={self.tekrar_dk}dk, "
                f"azami={self.azami}, bbox={self.bbox}")


# ---------------------------------------------------------------------------
# KAYNAK: OpenStreetMap / Overpass
# ---------------------------------------------------------------------------
def _secim_ifadeleri(sekiller):
    """'shop|amenity@restaurant,cafe' -> ['["shop"]', '["amenity"~"^(restaurant|cafe)$"]']."""
    ifadeler = []
    for token in [t.strip() for t in str(sekiller or "").split("|") if t.strip()]:
        if "@" in token:
            etiket, degerler = token.split("@", 1)
            desen = "^(" + "|".join(v.strip() for v in degerler.split(",") if v.strip()) + ")$"
            ifadeler.append(f'["{etiket.strip()}"~"{desen}"]')
        else:
            ifadeler.append(f'["{token}"]')
    return ifadeler


def overpass_metni(bbox, sekiller, azami):
    kutu = f"({bbox})"
    # nwr = node+way+relation: ayrı 'way' satırı yazmak sonucu iki katına çıkarır.
    satirlar = [f'nwr{ifades}{kutu};' for ifades in _secim_ifadeleri(sekiller)]
    return ("[out:json][timeout:45];"
            f"({''.join(satirlar)});"
            f"out tags center {int(azami)};")


def _adres_etiketleri(t):
    parca = [t.get("addr:street"), t.get("addr:housenumber"), t.get("addr:suburb"),
             t.get("addr:city"), t.get("addr:postcode")]
    metin = ", ".join(str(p).strip() for p in parca if p and str(p).strip())
    return metin or str(t.get("addr:full") or "").strip()


def _telefon_etiketleri(t):
    return (str(t.get("phone") or t.get("contact:phone") or
                t.get("contact:mobile") or "").strip())


def osm_adaylari(cevap, kaynak_etiketi="OSM"):
    """Ham Overpass JSON'undan aday sözlükleri üretir (ağ işi yok, test edilebilir)."""
    adaylar = []
    gorulen = set()
    for el in (cevap or {}).get("elements", []):
        t = el.get("tags") or {}
        # Yalnizca 'name': kategori etiketi ('restaurant') isletme adi degildir,
        # havuza 'Restoran' diye cinur ve panelde gercek bir firma sanilir.
        ad = str(t.get("name") or "").strip()
        if not ad:
            continue
        telefon = _telefon_etiketleri(t)
        adres = _adres_etiketleri(t)
        anahtar = telefon_kanonik(telefon) or f"{ad.lower()}|{adres.lower()}"
        if anahtar in gorulen:
            continue
        gorulen.add(anahtar)
        adaylar.append({
            "isletme": ad[:160],
            "telefon": telefon[:40],
            "adres": adres[:240],
            "kaynak": f"{kaynak_etiketi}:{el.get('type')}/{el.get('id')}",
        })
    return adaylar


def _http_post(url, veri, timeout):
    istek = urllib.request.Request(
        url, data=urllib.parse.urlencode({"data": veri}).encode(),
        headers={"User-Agent": "TRM-aday-havuzu/1.0 (aday havuzu; gonderim yok)",
                 "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(istek, timeout=timeout) as yanit:
        return json.loads(yanit.read().decode("utf-8", "replace"))


def osm_cek(yapi, log=None, ac=None):
    """Ağdan adayları çeker; tüm sunucular düşerse boş liste (tarama patlamaz)."""
    ac = ac or _http_post
    soru = overpass_metni(yapi.bbox, yapi.sekiller, yapi.azami)
    for url in yapi.url:
        try:
            cevap = ac(url, soru, yapi.dinle_sn)
        except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as hata:
            if log:
                log(f"[ADAY] {url.split('/')[2]} okunamadi ({type(hata).__name__}: {str(hata)[:80]})")
            continue
        adaylar = osm_adaylari(cevap)
        if adaylar:
            return adaylar, url
        if log:
            log(f"[ADAY] {url.split('/')[2]} bos dondu; siradaki sunucu")
    return [], ""


# ---------------------------------------------------------------------------
# KAYNAK: operatörün kendi listesi (CSV: isletme,telefon,adres)
# ---------------------------------------------------------------------------
def csv_adaylari(yol):
    if not yol or not os.path.isfile(yol):
        return []
    adaylar = []
    with open(yol, newline="", encoding="utf-8-sig") as fh:
        for i, satir in enumerate(csv.DictReader(fh)):
            kucuk = {(str(k or "").strip().lower()): v for k, v in satir.items()}
            ad = str(kucuk.get("isletme") or kucuk.get("ad") or kucuk.get("name") or "").strip()
            if not ad:
                continue
            adaylar.append({
                "isletme": ad[:160],
                "telefon": str(kucuk.get("telefon") or kucuk.get("phone") or "").strip()[:40],
                "adres": str(kucuk.get("adres") or kucuk.get("address") or "").strip()[:240],
                "kaynak": f"liste:{os.path.basename(yol)}#{i + 1}",
            })
    return adaylar


# ---------------------------------------------------------------------------
# HAVUZA YAZ (burada gonderim yok; yalnizca kayit)
# ---------------------------------------------------------------------------
def _kod(kanonik, ad, adres):
    oz = kanonik or f"{ad.lower().strip()}|{adres.lower().strip()}"
    return "ADAY-" + hashlib.sha1(oz.encode("utf-8")).hexdigest()[:12].upper()


def adaylari_ala(conn, adaylar):
    """Adayları esnaflar tablosuna izin=0 / durum='ADAY' olarak yazar.

    Dönen özet sayaçları panelde gösterilir; hiçbir dal 'gonderildi' yazmaz.
    """
    conn.create_function("kanonik", 1, telefon_kanonik)
    ozet = {"eklenen": 0, "atlanan_duplike": 0, "atlanan_kara_liste": 0,
            "atlanan_eksik": 0, "mevcut_dokunulmadi": 0}
    gorulen = set()
    for aday in adaylar or []:
        ad = str(aday.get("isletme") or "").strip()
        if not ad:
            ozet["atlanan_eksik"] += 1
            continue
        adres = str(aday.get("adres") or "").strip()
        telefon = str(aday.get("telefon") or "").strip()
        kanonik = telefon_kanonik(telefon)
        if kanonik and kara_listede_mi(conn, kanonik):
            ozet["atlanan_kara_liste"] += 1
            continue
        anahtar = kanonik or f"{ad.lower()}|{adres.lower()}"
        if anahtar in gorulen:
            ozet["atlanan_duplike"] += 1
            continue
        gorulen.add(anahtar)
        try:
            if kanonik:
                var = conn.execute(
                    "SELECT id FROM esnaflar WHERE kanonik(COALESCE(telefon, '')) = ?",
                    (kanonik,),
                ).fetchone()
            else:
                var = conn.execute(
                    "SELECT id FROM esnaflar WHERE LOWER(TRIM(isletme)) = LOWER(?) "
                    "AND TRIM(COALESCE(adres, '')) = TRIM(?)",
                    (ad, adres),
                ).fetchone()
            if var:
                # Mevcut satıra dokunulmaz: izin/opt_out/durum operatörün kararı.
                ozet["mevcut_dokunulmadi"] += 1
                continue
            conn.execute(
                "INSERT INTO esnaflar (isletme, telefon, kod, adres, durum, durum_kilit, "
                "izin, gonderim_durumu, kayit_tarihi) "
                "VALUES (?, ?, ?, ?, ?, 0, 0, 'gonderime_hazir', ?)",
                (ad, telefon, _kod(kanonik, ad, adres), adres, ADAY_DURUM,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            ozet["eklenen"] += 1
        except sqlite3.IntegrityError:
            ozet["atlanan_duplike"] += 1
        except sqlite3.Error:
            ozet["atlanan_eksik"] += 1
    return ozet


def ozet_yaz(conn, ozet, kaynak):
    try:
        conn.execute(
            "INSERT INTO otonom_durum (anahtar, deger) VALUES (?, ?) "
            "ON CONFLICT(anahtar) DO UPDATE SET deger = excluded.deger",
            (OZET_ANAHTAR, json.dumps({**ozet, "kaynak": kaynak,
                                       "zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                                      ensure_ascii=False)),
        )
        conn.commit()
    except sqlite3.Error:
        pass


def ozet_oka(conn):
    try:
        row = conn.execute("SELECT deger FROM otonom_durum WHERE anahtar = ?", (OZET_ANAHTAR,)).fetchone()
    except sqlite3.Error:
        return None
    if not row:
        return None
    try:
        return json.loads(row[0])
    except (TypeError, ValueError):
        return None


def tarama_calistir(baglan, yapi, log=None, cekici=None):
    """Bir tarama turu: çek -> havuza yaz -> özet bırak.

    Ağ hatası burada YUKARI fırlar; aday_tarama_dongusu yakalar ve döngüyü
    yaşatır. Bağlantı her hâlde kapatılır (yarım yazım olmaz).
    """
    conn = baglan()
    try:
        sema_goc_uygula(conn)  # kara_liste + izin kolonu yoksa üret (idempotent)
        adaylar, kaynak = (cekici or osm_cek)(yapi, log)
        ozet = adaylari_ala(conn, adaylar)
        ozet["aday_sayisi"] = len(adaylar)
        ozet_yaz(conn, ozet, kaynak)
        if log:
            host = kaynak.split("/")[2] if kaynak else "-"
            log(f"[ADAY] tarama bitti | kaynak={host} bulunan={len(adaylar)} "
                f"eklenen={ozet['eklenen']} kara-liste={ozet['atlanan_kara_liste']} "
                f"duplike={ozet['atlanan_duplike']} mevcut={ozet['mevcut_dokunulmadi']} "
                "(hepsi izin=0 -> gonderim sirasi DEGIL)")
        return ozet
    finally:
        conn.close()


def aday_tarama_dongusu(baglan, yapi, log, cekici=None, uyustur=time.sleep):
    """7/24 aday toplayıcı. ADAY_TARAMA=0 ise hiç çalışmaz (gönderimle ilgisi yok)."""
    if not yapi.tarama_acik:
        log(f"[ADAY] KAPALI (ADAY_TARAMA=0) | {yapi.sozler()}")
        return
    log(f"[ADAY] Aday havuzu taramasi başlatıldı | {yapi.sozler()} | lisans: {OSM_LISANS}")
    while True:
        bekleme_dk = yapi.aralik_dk
        try:
            ozet = tarama_calistir(baglan, yapi, log, cekici)
            if not ozet.get("aday_sayisi"):
                bekleme_dk = yapi.tekrar_dk
                log(f"[ADAY] kaynaklardan firma alinamadi -> {bekleme_dk} dk sonra tekrar denenecek")
        except Exception as hata:
            log(f"[ADAY HATA] {type(hata).__name__}: {hata} | {yapi.tekrar_dk} dk sonra tekrar")
            bekleme_dk = yapi.tekrar_dk
        uyustur(max(1, bekleme_dk) * 60)


def havuz_durumu(conn, limit=500):
    """Panel: havuzdaki adaylar (izin=0) ve özet. Salt-okur."""
    tablo_var = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='otonom_durum'").fetchone()
    ozet = ozet_oka(conn) if tablo_var else None
    try:
        kayitlar = [dict(r) for r in conn.execute(
            "SELECT id, isletme, telefon, adres, kod, durum, kayit_tarihi "
            "FROM esnaflar WHERE durum = ? AND COALESCE(izin, 0) = 0 "
            # Telefonsuz aday onaylansa da motor seçemez: önce arayabileceğin
            # numaralar listede olsun.
            "ORDER BY CASE WHEN TRIM(COALESCE(telefon, '')) = '' THEN 1 ELSE 0 END, "
            "id DESC LIMIT ?", (ADAY_DURUM, limit)).fetchall()]
        sayilar = conn.execute(
            "SELECT COUNT(*) AS toplam, "
            "SUM(CASE WHEN TRIM(COALESCE(telefon,''))<>'' THEN 1 ELSE 0 END) AS telefonlu, "
            "SUM(CASE WHEN TRIM(COALESCE(adres,''))<>'' THEN 1 ELSE 0 END) AS adresli "
            "FROM esnaflar WHERE durum = ? AND COALESCE(izin,0) = 0", (ADAY_DURUM,)
        ).fetchone()
        # Operatör havuzdan izin verdikçe burada büyür; 0 ise havuzda gönderim
        # sırasına girmiş tek kayıt yoktur.
        izin_verilmis = conn.execute(
            "SELECT COUNT(*) FROM esnaflar WHERE durum = ? AND COALESCE(izin,0) = 1",
            (ADAY_DURUM,)).fetchone()[0]
    except sqlite3.Error:
        kayitlar, sayilar, izin_verilmis = [], {}, 0
    return {
        "ozet": ozet,
        "toplam": (sayilar["toplam"] if sayilar else 0) or 0,
        "telefonlu": (sayilar["telefonlu"] if sayilar else 0) or 0,
        "adresli": (sayilar["adresli"] if sayilar else 0) or 0,
        "izin_verilmis": izin_verilmis or 0,
        "atıf": OSM_LISANS,
        "kayitlar": kayitlar,
    }


if __name__ == "__main__":
    # Tek seferlik tarama / kaynak denemesi:
    #   python aday_havuzu.py --kuru-run        (hiçbir şey yazmaz, sadece sayar)
    #   python aday_havuzu.py                   (canli trm_veritabani.db -> izin=0)
    #   python aday_havuzu.py --liste kendi.csv (operatör listesi)
    import argparse
    import sqlite3 as _sql

    arg = argparse.ArgumentParser(description="TRM aday havuzu (toplama; gonderim YOK)")
    arg.add_argument("--kuru-run", action="store_true", help="ağdan oku, DB'ye yazma")
    arg.add_argument("--liste", help="CSV: isletme,telefon,adres")
    arg.add_argument("--db", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "trm_veritabani.db"))
    arg.add_argument("--bbox")
    opts = arg.parse_args()

    yapi_ = AdayYapisi()
    if opts.bbox:
        yapi_.bbox = opts.bbox
    if opts.liste:
        bulunan = csv_adaylari(opts.liste)
    else:
        bulunan, _ = osm_cek(yapi_, log=print)
    print(f"bulunan aday: {len(bulunan)} | telefonlu: "
          f"{sum(1 for x in bulunan if x['telefon'])} | adresli: "
          f"{sum(1 for x in bulunan if x['adres'])}")
    print("ornek:", [x["isletme"] for x in bulunan[:8]])
    if opts.kuru_run:
        print("KURU RUN: veritabanina yazilmadi.")
        raise SystemExit(0)
    _conn = _sql.connect(opts.db)
    _conn.row_factory = _sql.Row
    sema_goc_uygula(_conn)
    print("ozet:", adaylari_ala(_conn, bulunan))
    print("havuz:", {k: v for k, v in havuz_durumu(_conn).items() if k != "kayitlar"})
    _conn.close()
