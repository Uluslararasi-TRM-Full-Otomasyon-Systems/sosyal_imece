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
  * `kod` UNIQUE olduğu için çakışan satır atlanır, overwrite edilmez;
  * mahalle/ilçe/koordinat YALNIZCA OSM etiketinden geldiği gibi yazılır —
    etiket yoksa alan NULL kalır, asla tahmin edilmez;
  * il sınırı (bbox) alınamazsa veya karo sayısı bütçeyi aşarsa tarama
    YAPILMAZ; uydurma kapsama yerine boş tur loglanır.

Ölçekleme (Aydın geneli): ilin idari sınır kutusu Overpass'tan okunur, kutu
~ADAY_TILE_KM kenarlı karolara (bbox dizisi) bölünür ve her tur yalnızca
ADAY_TUR_KARO_AZAMI karo / ADAY_TUR_SN saniye işler; imleç veritabanındaki
özet içinde saklanır, sonraki tur kaldığı karo devam eder. Böylece geniş bir
il, tek bir uzun istekte Overpass kuyruğunda boğulmadan sırayla taranır.
"""

import csv
import hashlib
import json
import math
import os
import re
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
_VARSAYILAN_BOLGE = "Aydın"
# 1° enlem ~111.32 km; 1° boylam ~111.41*cos(enlem) km.
_KM_LAT = 111.32
_KM_LON = 111.41
# İdari ad Only letters/spaces/hyphens: sorguya noktalı virgül ya da tırnak
# sızması Overpass ifadesini bozar (veya başka bir sorgu çalıştırır).
_BOLGE_AD = re.compile(r"^[A-Za-zÇĞİÖŞÜçğıöşü][A-Za-zÇĞİÖŞÜçğıöşü .\-]{1,39}$")


class KaroHatasi(ValueError):
    """Karo dizisi bütçeyi aşıyor: tarama yapılmaz, operatör kararı gerekir."""

    def __init__(self, karo_sayisi, azami):
        super().__init__(f"karo dizisi {karo_sayisi} > ADAY_KARO_AZAMI={azami}")
        self.karo_sayisi = karo_sayisi
        self.azami = azami


def _bayrak(deger, varsayilan=False):
    if deger is None:
        return varsayilan
    return str(deger).strip().lower() in ("1", "true", "evet", "on", "open", "acik")


def _sayic(deger, varsayilan):
    try:
        return int(str(deger).strip())
    except (TypeError, ValueError):
        return varsayilan


def _ondalik(deger, varsayilan):
    try:
        return float(str(deger).strip())
    except (TypeError, ValueError):
        return varsayilan


def _metin(*aday_degerler):
    """İlk dolu etiketi döndürür (OSM etiketi yoksa None -> tahmin yok)."""
    for deger in aday_degerler:
        metin = str(deger or "").strip()
        if metin:
            return metin[:120]
    return None


def _kosay(deger):
    try:
        return round(float(str(deger).strip()), 6)
    except (TypeError, ValueError):
        return None


def _bbox_ayikla(deger):
    """'minlat,minlon,maxlat,maxlon' -> tuple | None. Geçersizse None (fail-closed)."""
    if not deger:
        return None
    try:
        parcalar = [float(p) for p in str(deger).replace(" ", "").split(",")]
    except ValueError:
        return None
    if len(parcalar) != 4:
        return None
    minlat, minlon, maxlat, maxlon = parcalar
    if not (-90 <= minlat < maxlat <= 90 and -180 <= minlon < maxlon <= 180):
        return None
    return minlat, minlon, maxlat, maxlon


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
        # --- karo (tile) taraması: il geneli ölçekleme -----------------------
        self.karo_acik = _bayrak(e.get("ADAY_KARO_TARAMA"), True)
        self.bolge = str(e.get("ADAY_BOLGE") or _VARSAYILAN_BOLGE).strip()
        # Elle verilirse idari sınır sorgusu hiç yapılmaz (Overpass'a 1 istek
        # azalır); yanlış kutu = yanlış kapsama, o yüzden geçersiz giriş None.
        self.bolge_bbox = _bbox_ayikla(e.get("ADAY_BOLGE_BBOX"))
        self.tile_km = min(50.0, max(1.0, _ondalik(e.get("ADAY_TILE_KM"), 8.0)))
        self.tile_sn = max(10, _sayic(e.get("ADAY_TILE_SN"), 60))
        # Bir turun bütçesi: karo sayısı VE saniye. Aşılınca imleç sonraki
        # karoda bırakılır; sonraki tur oradan devam eder.
        self.tur_karo_azami = max(1, _sayic(e.get("ADAY_TUR_KARO_AZAMI"), 24))
        self.tur_sn = max(60, _sayic(e.get("ADAY_TUR_SN"), 900))
        # absolute grid cap: yazım hatasıyla il yerine kıta kutusu girerse
        # tarama hiç yapılmaz (100bin istek yerine 0 istek).
        self.karo_azami = max(1, _sayic(e.get("ADAY_KARO_AZAMI"), 400))
        self.karo_bekleme_sn = max(0, _sayic(e.get("ADAY_KARO_BEKLEME_SN"), 3))
        # tarama_calistir() bunu özetten geri yükler (turlar arası kaldığın yer)
        self.karo_imleci = 0
        self.son_kapsama = {}

    def sozler(self):
        if self.karo_acik:
            yer = (f"bolge={self.bolge} (karo {self.tile_km}km, "
                   f"tur<= {self.tur_karo_azami} karo/{self.tur_sn}sn)")
        else:
            yer = f"bbox={self.bbox} (tek kutu)"
        return (f"tarama={'ACIK' if self.tarama_acik else 'KAPALI'}, "
                f"aralik={self.aralik_dk}dk, tekrar={self.tekrar_dk}dk, "
                f"azami={self.azami}, {yer}")


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


def bolge_bbox_metni(bolge):
    """İl sınır kutusunu soran Overpass ifadesi (ad regex'ten geçmiş olmalı).

    Tek istekte hem admin_level=4 (il) hem de herhangi bir idari sınır denenir:
    yoğun Overpass kuyruğunda her ek istek dakikalara mal olur.
    """
    return ("[out:json][timeout:25];"
            f'(rel["boundary"="administrative"]["admin_level"="4"]["name"="{bolge}"];'
            f'rel["boundary"="administrative"]["name"="{bolge}"];);'
            "out bb 1;")


def bolge_bbox_ayikla(cevap):
    """'out bb' cevabından (minlat,minlon,maxlat,maxlon); yoksa None."""
    for el in (cevap or {}).get("elements", []):
        b = el.get("bounds") or {}
        if all(k in b for k in ("minlat", "minlon", "maxlat", "maxlon")):
            kutu = _bbox_ayikla(", ".join(f"{float(b[k]):.6f}" for k in
                                          ("minlat", "minlon", "maxlat", "maxlon")))
            if kutu:
                return kutu
    return None


def osm_bolge_bbox(yapi, log=None, ac=None):
    """İlin GERÇEK sınır kutusu (Overpass idari sınır). Alınamazsa None.

    None -> karo taraması yapılmaz: uydurma bir kutuyla 'il tarandı' demek,
    olmayan kapsamanın raporu olurdu.
    """
    if yapi.bolge_bbox:
        return yapi.bolge_bbox
    ac = ac or _http_post
    if not _BOLGE_AD.match(str(yapi.bolge or "").strip()):
        if log:
            log(f"[ADAY] il adı geçersiz ({str(yapi.bolge)[:40]!r}) -> karo taraması YOK")
        return None
    soru = bolge_bbox_metni(str(yapi.bolge).strip())
    for url in yapi.url:
        try:
            cevap = ac(url, soru, min(60, yapi.dinle_sn))
        except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as hata:
            if log:
                log(f"[ADAY] sınır kutusu {url.split('/')[2]} okunamadi "
                    f"({type(hata).__name__}: {str(hata)[:60]})")
            continue
        kutu = bolge_bbox_ayikla(cevap)
        if kutu:
            if log:
                log(f"[ADAY] {yapi.bolge} sınır kutusu: {kutu} "
                    f"(karo {yapi.tile_km}km)")
            return kutu
    if log:
        log(f"[ADAY] '{yapi.bolge}' için idari sınır bulunamadı")
    return None


def karo_bboxlari(bbox, tile_km, azami=None):
    """Kutuyu ~tile_km kenarlı karolara böler -> ['minlat,minlon,maxlat,maxlon', ...]

    Boylam adımı her şeritte yeniden hesaplanır: 1° boylam enleme göre daralır
    (111.41*cos(lat) km). Sabit adım kullanmak kuzeydeki kareleri doğuya
    kaydırıp karo aralarında taranmamış şerit bırakırdı.
    """
    minlat, minlon, maxlat, maxlon = bbox
    dlat = tile_km / _KM_LAT
    karolar = []
    lat = minlat
    while lat < maxlat - 1e-9:
        lat2 = min(maxlat, lat + dlat)
        km_deg_boylam = _KM_LON * max(0.02, math.cos(math.radians((lat + lat2) / 2.0)))
        dlon = tile_km / km_deg_boylam
        lon = minlon
        while lon < maxlon - 1e-9:
            lon2 = min(maxlon, lon + dlon)
            karolar.append(f"{lat:.6f},{lon:.6f},{lat2:.6f},{lon2:.6f}")
            if azami is not None and len(karolar) > azami:
                raise KaroHatasi(len(karolar), azami)
            lon = lon2
        lat = lat2
    return karolar


def _adres_etiketleri(t):
    parca = [t.get("addr:street"), t.get("addr:housenumber"), t.get("addr:suburb"),
             t.get("addr:city"), t.get("addr:postcode")]
    metin = ", ".join(str(p).strip() for p in parca if p and str(p).strip())
    return metin or str(t.get("addr:full") or "").strip()


def _telefon_etiketleri(t):
    return (str(t.get("phone") or t.get("contact:phone") or
                t.get("contact:mobile") or "").strip())


# Türkiye OSM adres şemasında ilçe/mahalle etiketleri karışık kullanılıyor;
# hangisi varsa o alınır, hiçbiri yoksa alan NULL kalır (tahmin yok).
def _ilce_etiketleri(t):
    return _metin(t.get("addr:district"), t.get("addr:subdistrict"),
                  t.get("addr:county"), t.get("is_in:district"))


def _mahalle_etiketleri(t):
    return _metin(t.get("addr:quarter"), t.get("addr:neighbourhood"),
                  t.get("addr:suburb"), t.get("is_in:quarter"))


def _koordinat(el):
    merkez = el.get("center") or {}
    return _kosay(el.get("lat") if el.get("lat") is not None else merkez.get("lat")), \
        _kosay(el.get("lon") if el.get("lon") is not None else merkez.get("lon"))


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
        enlem, boylam = _koordinat(el)
        adaylar.append({
            "isletme": ad[:160],
            "telefon": telefon[:40],
            "adres": adres[:240],
            "kaynak": f"{kaynak_etiketi}:{el.get('type')}/{el.get('id')}",
            "ilce": _ilce_etiketleri(t),
            "mahalle": _mahalle_etiketleri(t),
            "enlem": enlem,
            "boylam": boylam,
        })
    return adaylar


def _http_post(url, veri, timeout):
    istek = urllib.request.Request(
        url, data=urllib.parse.urlencode({"data": veri}).encode(),
        headers={"User-Agent": "TRM-aday-havuzu/1.0 (aday havuzu; gonderim yok)",
                 "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(istek, timeout=timeout) as yanit:
        return json.loads(yanit.read().decode("utf-8", "replace"))


def _karo_ara(karo, yapi, ac, log=None, sessiz=False, dinle=None):
    """Tek karo: aynalar üzerinde dener. (adaylar, url) | ([], '')."""
    soru = overpass_metni(karo, yapi.sekiller, yapi.azami)
    # Küçük karo kısa dinler; tek kutuya düşülen tarama eski (240sn) limitini korur.
    dinle = dinle or (yapi.tile_sn if yapi.karo_acik else yapi.dinle_sn)
    for url in yapi.url:
        try:
            cevap = ac(url, soru, dinle)
        except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as hata:
            if log:
                log(f"[ADAY] {url.split('/')[2]} okunamadi ({type(hata).__name__}: {str(hata)[:80]})")
            continue
        adaylar = osm_adaylari(cevap)
        if adaylar:
            return adaylar, url
        if log and not sessiz:
            log(f"[ADAY] {url.split('/')[2]} bos dondu; siradaki sunucu")
    return [], ""


def _bolge_karolari(yapi, ac, log):
    """(karolar, mod) — KARO: il geneli | TEK_KUTU: ADAY_BBOX | RED: tarama yok."""
    if not yapi.karo_acik:
        return [yapi.bbox], "TEK_KUTU"
    kutu = yapi.bolge_bbox or osm_bolge_bbox(yapi, log, ac)
    if not kutu:
        if log:
            log(f"[ADAY] '{yapi.bolge}' sinir kutusu alinamadi -> karo taramasi YOK, "
                f"tek kutuya dusuluyor: {yapi.bbox}")
        return [yapi.bbox], "TEK_KUTU"
    try:
        return karo_bboxlari(kutu, yapi.tile_km, yapi.karo_azami), "KARO"
    except KaroHatasi as hata:
        if log:
            log(f"[ADAY] {hata} | tarama YAPILMADI (uydurma kapsama yok). "
                f"Bolgeyi daraltin (ADAY_BOLGE) ya da tile buyutun (ADAY_TILE_KM).")
        return [], "RED"


def osm_cek(yapi, log=None, ac=None, uyustur=None, zaman=None):
    """Ağdan adayları çeker; tüm sunucular düşerse boş liste (tarama patlamaz).

    Karo modunda tek dev istek yerine bbox dizisi taranır ve tur bütçesiyle
    (ADAY_TUR_KARO_AZAMI / ADAY_TUR_SN) sınırlanır; imleç yapi.karo_imleci
    üzerinde kalır, tarama_calistir() onu özetten geri yükler.
    """
    ac = ac or _http_post
    uyustur = uyustur or time.sleep
    zaman = zaman or time.monotonic
    karolar, mod = _bolge_karolari(yapi, ac, log)
    yapi.son_kapsama = {"mod": mod, "bolge": yapi.bolge if mod == "KARO" else None,
                        "karo_toplam": len(karolar), "karo_islenen": 0,
                        "imleç": yapi.karo_imleci}
    if not karolar:
        return [], ""
    adet = len(karolar)
    bitis = zaman() + yapi.tur_sn
    dinle = yapi.tile_sn if mod == "KARO" else yapi.dinle_sn
    adaylar = []
    gorulen = set()
    kaynak = ""
    islenen = 0
    baslangic = yapi.karo_imleci % adet   # imleç döngü içinde ilerler, sabit başlangıç lazım
    for i in range(adet):
        if islenen >= yapi.tur_karo_azami or (mod == "KARO" and zaman() >= bitis):
            break
        idx = (baslangic + i) % adet
        bulunan, url = _karo_ara(karolar[idx], yapi, ac, log,
                                 sessiz=(mod == "KARO"), dinle=dinle)
        for aday in bulunan:
            anahtar = (telefon_kanonik(aday["telefon"]) or
                       f"{aday['isletme'].lower()}|{aday['adres'].lower()}")
            if anahtar in gorulen:
                continue
            gorulen.add(anahtar)
            adaylar.append(aday)
        if bulunan and not kaynak:
            kaynak = url
        islenen += 1
        yapi.karo_imleci = (idx + 1) % adet
        if islenen < min(adet, yapi.tur_karo_azami) and yapi.karo_bekleme_sn:
            uyustur(yapi.karo_bekleme_sn)
    yapi.son_kapsama.update({"karo_islenen": islenen, "imleç": yapi.karo_imleci})
    if log and mod == "KARO":
        log(f"[ADAY] karo turu bitti | bulunan={len(adaylar)} "
            f"karo={islenen}/{adet} sonraki-imleç={yapi.karo_imleci}")
    return adaylar, kaynak


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
                "ilce": _metin(kucuk.get("ilce") or kucuk.get("district")),
                "mahalle": _metin(kucuk.get("mahalle") or kucuk.get("quarter")),
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
                "izin, gonderim_durumu, kayit_tarihi, ilce, mahalle, enlem, boylam, kaynak) "
                "VALUES (?, ?, ?, ?, ?, 0, 0, 'gonderime_hazir', ?, ?, ?, ?, ?, ?)",
                (ad, telefon, _kod(kanonik, ad, adres), adres, ADAY_DURUM,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 aday.get("ilce"), aday.get("mahalle"),
                 _kosay(aday.get("enlem")), _kosay(aday.get("boylam")),
                 str(aday.get("kaynak") or "")[:200] or None),
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

    Karo imleci özetin içinde saklanır: il geneli bir tura sığmaz, her tur
    kaldığı karodan devam eder (kapsama rotasyonu buradan gelir).
    """
    conn = baglan()
    try:
        sema_goc_uygula(conn)  # kara_liste + izin kolonu yoksa üret (idempotent)
        onceki = ozet_oka(conn) or {}
        yapi.karo_imleci = max(0, _sayic(onceki.get("karo_imleci"), 0))
        adaylar, kaynak = (cekici or osm_cek)(yapi, log)
        ozet = adaylari_ala(conn, adaylar)
        ozet["aday_sayisi"] = len(adaylar)
        ozet["kapsama"] = dict(getattr(yapi, "son_kapsama", None) or {})
        ozet["karo_imleci"] = getattr(yapi, "karo_imleci", 0)
        ozet_yaz(conn, ozet, kaynak)
        if log:
            host = kaynak.split("/")[2] if kaynak else "-"
            kapsama = ozet["kapsama"]
            karo = (f" karo={kapsama.get('karo_islenen')}/{kapsama.get('karo_toplam')}"
                    f" sonraki={kapsama.get('imleç')}") if kapsama.get("mod") == "KARO" else ""
            log(f"[ADAY] tarama bitti | kaynak={host} bulunan={len(adaylar)} "
                f"eklenen={ozet['eklenen']} kara-liste={ozet['atlanan_kara_liste']} "
                f"duplike={ozet['atlanan_duplike']} mevcut={ozet['mevcut_dokunulmadi']}"
                f"{karo} "
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


def _filtre_sql(degerler):
    """(where parçaları, parametreler) — ilce/mahalle için parametreli eşleştirme."""
    kosul, params = [], []
    for kolon, deger in degerler:
        metin = str(deger or "").strip()
        if metin:
            kosul.append(f"LOWER(TRIM(COALESCE({kolon}, ''))) = LOWER(?)")
            params.append(metin)
    return (" AND " + " AND ".join(kosul) if kosul else ""), params


def havuz_durumu(conn, limit=500, ilce=None, mahalle=None):
    """Panel: havuzdaki adaylar (izin=0) ve özet. Salt-okur.

    Filtre YALNIZCA esnaflar satırlarındaki OSM/liste etiketlerine uygulanır;
    dışarıdan tüketici veya demografik hedef listesi çekilmez.
    """
    filtre, params = _filtre_sql([("ilce", ilce), ("mahalle", mahalle)])
    tablo_var = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='otonom_durum'").fetchone()
    ozet = ozet_oka(conn) if tablo_var else None
    try:
        kayitlar = [dict(r) for r in conn.execute(
            "SELECT id, isletme, telefon, adres, kod, durum, kayit_tarihi, "
            "ilce, mahalle, enlem, boylam, kaynak "
            "FROM esnaflar WHERE durum = ? AND COALESCE(izin, 0) = 0" + filtre + " "
            # Telefonsuz aday onaylansa da motor seçemez: önce arayabileceğin
            # numaralar listede olsun.
            "ORDER BY CASE WHEN TRIM(COALESCE(telefon, '')) = '' THEN 1 ELSE 0 END, "
            "id DESC LIMIT ?", (ADAY_DURUM, *params, limit)).fetchall()]
        sayilar = conn.execute(
            "SELECT COUNT(*) AS toplam, "
            "SUM(CASE WHEN TRIM(COALESCE(telefon,''))<>'' THEN 1 ELSE 0 END) AS telefonlu, "
            "SUM(CASE WHEN TRIM(COALESCE(adres,''))<>'' THEN 1 ELSE 0 END) AS adresli, "
            "SUM(CASE WHEN TRIM(COALESCE(mahalle,''))<>'' THEN 1 ELSE 0 END) AS mahalleli "
            "FROM esnaflar WHERE durum = ? AND COALESCE(izin,0) = 0" + filtre,
            (ADAY_DURUM, *params)
        ).fetchone()
        # Operatör havuzdan izin verdikçe burada büyür; 0 ise havuzda gönderim
        # sırasına girmiş tek kayıt yoktur.
        izin_verilmis = conn.execute(
            "SELECT COUNT(*) FROM esnaflar WHERE durum = ? AND COALESCE(izin,0) = 1" + filtre,
            (ADAY_DURUM, *params)).fetchone()[0]
    except sqlite3.Error:
        kayitlar, sayilar, izin_verilmis = [], {}, 0
    return {
        "ozet": ozet,
        "toplam": (sayilar["toplam"] if sayilar else 0) or 0,
        "telefonlu": (sayilar["telefonlu"] if sayilar else 0) or 0,
        "adresli": (sayilar["adresli"] if sayilar else 0) or 0,
        "mahalleli": (sayilar["mahalleli"] if sayilar else 0) or 0,
        "izin_verilmis": izin_verilmis or 0,
        "atıf": OSM_LISANS,
        "filtre": {"ilce": str(ilce or "").strip() or None,
                   "mahalle": str(mahalle or "").strip() or None},
        "kayitlar": kayitlar,
    }


def bolge_dagilimi(conn, limit=200):
    """Havuzdaki esnaf kayıtlarının ilçe/mahalle kırılımı (salt-okur, OSM etiketi).

    Yalnızca `esnaflar` tablosundaki satırlar sayılır; etiketi boş olan kayıt
    'biliniyor' gibi gösterilmez, (Etiketsiz) satırına toplanır.
    """
    try:
        satirlar = conn.execute(
            "SELECT TRIM(COALESCE(ilce, '')) AS ilce, TRIM(COALESCE(mahalle, '')) AS mahalle, "
            "COUNT(*) AS aday, "
            "SUM(CASE WHEN COALESCE(izin, 0) = 1 THEN 1 ELSE 0 END) AS izinli, "
            "SUM(CASE WHEN TRIM(COALESCE(telefon, '')) <> '' THEN 1 ELSE 0 END) AS telefonlu "
            "FROM esnaflar WHERE durum = ? "
            "GROUP BY ilce, mahalle "
            "ORDER BY aday DESC, ilce ASC LIMIT ?", (ADAY_DURUM, limit)).fetchall()
    except sqlite3.Error:
        return []
    return [{"ilce": (r["ilce"] or None), "mahalle": (r["mahalle"] or None),
             "aday": r["aday"] or 0, "izinli": r["izinli"] or 0,
             "telefonlu": r["telefonlu"] or 0} for r in satirlar]


if __name__ == "__main__":
    # Tek seferlik tarama / kaynak denemesi:
    #   python aday_havuzu.py --kuru-run        (hiçbir şey yazmaz, sadece sayar)
    #   python aday_havuzu.py                   (canli trm_veritabani.db -> izin=0)
    #   python aday_havuzu.py --liste kendi.csv (operatör listesi)
    import argparse
    import sqlite3 as _sql

    arg = argparse.ArgumentParser(description="TRM aday havuzu (toplama; gonderim YOK)")
    arg.add_argument("--kuru-run", action="store_true", help="ağdan oku, DB'ye yazma")
    arg.add_argument("--liste", help="CSV: isletme,telefon,adres[,ilce,mahalle]")
    arg.add_argument("--db", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "trm_veritabani.db"))
    arg.add_argument("--bbox", help="tek kutu tarama (ADAY_BBOX yerine)")
    arg.add_argument("--bolge", help="il geneli karo tarama (ornek: Aydin)")
    arg.add_argument("--tile-km", type=float, help="karo kenarı (km)")
    arg.add_argument("--karo-run", type=int, metavar="N",
                     help="yalnizca ilk N karo (tek seferlik tur denemesi)")
    arg.add_argument("--dagilim", action="store_true", help="ilce/mahalle kirilimini yazdir")
    arg.add_argument("--ilce")
    arg.add_argument("--mahalle")
    opts = arg.parse_args()

    yapi_ = AdayYapisi()
    if opts.bbox:
        yapi_.karo_acik = False
        yapi_.bbox = opts.bbox
    if opts.bolge:
        yapi_.karo_acik = True
        yapi_.bolge = opts.bolge
    if opts.tile_km:
        yapi_.tile_km = min(50.0, max(1.0, opts.tile_km))
    if opts.karo_run:
        yapi_.tur_karo_azami = max(1, opts.karo_run)
    if opts.dagilim and not (opts.kuru_run or opts.liste or opts.bbox or opts.bolge):
        _conn = _sql.connect(opts.db)
        _conn.row_factory = _sql.Row
        sema_goc_uygula(_conn)
        dagilim = bolge_dagilimi(_conn, limit=int(os.environ.get("ADAY_DAGILIM_LIMIT", 200)))
        print(f"{'ilce':<20} {'mahalle':<24} {'aday':>6} {'izinli':>7} {'telefonlu':>10}")
        if not dagilim:
            print("(havuzda aday kaydi yok)")
        for satir in dagilim:
            print(f"{str(satir['ilce'] or '(Etiketsiz)'):<20} "
                  f"{str(satir['mahalle'] or '(Etiketsiz)'):<24} {satir['aday']:>6} "
                  f"{satir['izinli']:>7} {satir['telefonlu']:>10}")
        print("atıf:", OSM_LISANS)
        _conn.close()
        raise SystemExit(0)
    if opts.liste:
        bulunan = csv_adaylari(opts.liste)
    else:
        bulunan, _ = osm_cek(yapi_, log=print)
    print(f"bulunan aday: {len(bulunan)} | telefonlu: "
          f"{sum(1 for x in bulunan if x['telefon'])} | adresli: "
          f"{sum(1 for x in bulunan if x['adres'])} | mahalleli: "
          f"{sum(1 for x in bulunan if x.get('mahalle'))}")
    print("kapsama:", getattr(yapi_, "son_kapsama", {}))
    print("ornek:", [x["isletme"] for x in bulunan[:8]])
    if opts.kuru_run:
        print("KURU RUN: veritabanina yazilmadi.")
        raise SystemExit(0)
    _conn = _sql.connect(opts.db)
    _conn.row_factory = _sql.Row
    sema_goc_uygula(_conn)
    print("ozet:", adaylari_ala(_conn, bulunan))
    print("havuz:", {k: v for k, v in havuz_durumu(
        _conn, ilce=opts.ilce, mahalle=opts.mahalle).items() if k != "kayitlar"})
    _conn.close()
