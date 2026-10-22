# -*- coding: utf-8 -*-
"""aday_havuzu.py testleri — ağdan BAĞIMSIZ (fetcher enjekte edilir).

Kritik güvence: havuzdan giren hiçbir kayıt gönderim sırasına düşmez. Testler
bunu hem izin kolonunun 0 kalmasıyla hem de otonom_motor.uygun_esnaflar()'ın
bu kayıtları hiç seçmemesiyle doğrular.

Not: tarama_calistir() üretim sözleşmesi gereği KENDI bağlantısını açar ve
kapatır; testler de bu yüzden yol üzerinden yeni bağlantı kullanır.
"""

import os
import re
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aday_havuzu as a  # noqa: E402
import otonom_motor as m  # noqa: E402

TUR = datetime(2026, 10, 19, 12, 0, 0, tzinfo=timezone.utc)

_CEVAP = {"elements": [
    {"type": "node", "id": 1, "tags": {
        "name": "Zeytin Cafe", "phone": "+90 530 111 22 33",
        "addr:street": "Ataturk Cad.", "addr:housenumber": "12", "addr:city": "Kusadasi"}},
    {"type": "node", "id": 2, "tags": {"name": "Sahil Balik", "contact:phone": "0532 444 55 66"}},
    {"type": "way", "id": 3, "tags": {"name": "Ada Kirtasiye", "addr:street": "Cumhuriyet Cad."}},
    {"type": "node", "id": 4, "tags": {"amenity": "restaurant"}},       # isimsiz -> atlanır
    {"type": "node", "id": 5, "tags": {"name": "Zeytin Cafe", "phone": "05301112233"}},  # duplike
]}


def _baglan(yol):
    conn = sqlite3.connect(yol)
    conn.row_factory = sqlite3.Row
    return conn


def _veritabani():
    """esnaflar tablasi + otonom göçü uygulanmış boş bir veritabanı yolu."""
    fd, yol = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = _baglan(yol)
    conn.execute("CREATE TABLE esnaflar (id INTEGER PRIMARY KEY AUTOINCREMENT, isletme TEXT, "
                 "telefon TEXT, kod TEXT UNIQUE, adres TEXT, durum TEXT DEFAULT 'GÖNDERİLDİ', "
                 "gelen_yanit TEXT, kayit_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP, "
                 "durum_kilit INTEGER DEFAULT 0)")
    conn.commit()
    a.sema_goc_uygula(conn)
    conn.close()
    return yol


def _yapi(**env):
    return a.AdayYapisi(env)


def _cekici(yapi, log=None):
    return a.osm_adaylari(_CEVAP), "https://overpass.example/api/interpreter"


def _tarayal(yol, yapi=None, cekici=_cekici):
    return a.tarama_calistir(lambda: _baglan(yol), yapi or _yapi(), log=lambda mesaj: None,
                             cekici=cekici)


def _hepsi(yol):
    conn = _baglan(yol)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM esnaflar ORDER BY id")]
    finally:
        conn.close()


def _uygunlar(yol):
    conn = _baglan(yol)
    try:
        return [x["id"] for x in m.uygun_esnaflar(conn, m.Yapilandirma({"OTONOM_GONDERIM": "1"}), TUR, 50)]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
def test_osm_etiketleri_adaya_donusur():
    adaylar = a.osm_adaylari(_CEVAP)
    assert [x["isletme"] for x in adaylar] == ["Zeytin Cafe", "Sahil Balik", "Ada Kirtasiye"], adaylar
    assert adaylar[0]["telefon"] == "+90 530 111 22 33"
    assert "Ataturk Cad" in adaylar[0]["adres"] and "Kusadasi" in adaylar[0]["adres"]
    assert adaylar[1]["telefon"] == "0532 444 55 66", "contact:phone da okunmali"
    assert adaylar[2]["telefon"] == "", "telefonsuz aday da havuza girer"


def test_havuz_asla_gonderim_sirasina_girmez():
    yol = _veritabani()
    try:
        ozet = _tarayal(yol)
        assert ozet["eklenen"] == 3 and ozet["aday_sayisi"] == 3, ozet
        satirlar = _hepsi(yol)
        assert len(satirlar) == 3
        for s in satirlar:
            assert s["izin"] == 0, f"aday havuzu izin=1 yazamaz: {s}"
            assert s["durum"] == a.ADAY_DURUM
        # Motor bu kayıtların HİÇBİRİNİ seçmez:
        assert _uygunlar(yol) == []
        # Eski (durum='onayli') süzen göndericiler de takılır:
        assert not any(s["durum"] == "onayli" for s in satirlar)
    finally:
        os.unlink(yol)


def test_kara_listedeki_numara_havuza_da_giremez():
    yol = _veritabani()
    conn = _baglan(yol)
    try:
        m.kara_listeye_ekle(conn, "905301112233", "opt-out mesaji: DUR", TUR)
    finally:
        conn.close()
    ozet = _tarayal(yol)
    assert ozet["atlanan_kara_liste"] == 1, ozet
    assert [s["isletme"] for s in _hepsi(yol)] == ["Sahil Balik", "Ada Kirtasiye"]
    # Reddetmiş numara panelde "aday" olarak bile görünmemeli. Panel sırası
    # operatörün iş akışına göre: arayabileceğin kayıt (telefonlu Sahil Balik)
    # önce, telefonsuz Ada Kirtasiye sonra gelir.
    conn = _baglan(yol)
    try:
        assert [k["isletme"] for k in a.havuz_durumu(conn)["kayitlar"]] == ["Sahil Balik", "Ada Kirtasiye"]
    finally:
        conn.close()


def test_ikinci_tarama_cogaltmaz_ve_operator_kararini_bozmaz():
    yol = _veritabani()
    _tarayal(yol)
    conn = _baglan(yol)
    try:
        # Operatör panelden adaya izin verildi (adres+telefon tam olan kayıt):
        conn.execute("UPDATE esnaflar SET izin=1, durum='onayli' WHERE isletme='Zeytin Cafe'")
        conn.commit()
    finally:
        conn.close()
    ozet = _tarayal(yol)
    assert ozet["eklenen"] == 0 and ozet["mevcut_dokunulmadi"] == 3, ozet
    assert len(_hepsi(yol)) == 3
    ze = [s for s in _hepsi(yol) if s["isletme"] == "Zeytin Cafe"][0]
    assert ze["izin"] == 1 and ze["durum"] == "onayli", "tarama izin/karar alanina dokunamaz"
    # İzin verilen tek aday sıraya girer; diğerleri izin=0 nedeniyle dışarıda:
    assert _uygunlar(yol) == [ze["id"]]


def test_opt_out_olmus_satir_taramayla_dirilmez():
    yol = _veritabani()
    conn = _baglan(yol)
    try:
        conn.execute("INSERT INTO esnaflar (isletme, telefon, kod, adres, izin, opt_out, "
                     "gonderim_durumu, durum) VALUES ('Sahil Balik','05324445566','TRM-1',"
                     "'Cumhuriyet Cad.',1,1,'opt_out','opt_out')")
        conn.commit()
    finally:
        conn.close()
    ozet = _tarayal(yol)
    assert ozet["mevcut_dokunulmadi"] == 1 and ozet["eklenen"] == 2, ozet
    satir = [s for s in _hepsi(yol) if s["isletme"] == "Sahil Balik"][0]
    assert satir["opt_out"] == 1 and satir["durum"] == "opt_out", "aday etiketiyle geri alınamaz"
    assert _uygunlar(yol) == []


def test_overpass_sorusu_bbox_ve_etiketleri_icerir():
    soru = a.overpass_metni("37.80,27.15,37.92,27.40", _yapi().sekiller, 300)
    assert "(37.80,27.15,37.92,27.40)" in soru
    assert '["shop"]' in soru
    assert '["amenity"~"^(restaurant|cafe|bar|fast_food|pharmacy|bakery)$"]' in soru
    assert soru.rstrip().endswith("out tags center 300;")
    assert "nwr[" in soru and "way[" not in soru, "nwr nod+yol+iliski zaten kapsar"
    assert ";;" not in soru, "bos Overpass ifadesi parse hatasi verir"


def test_dongu_hata_dayanikli_ve_araliga_uyar():
    yol = _veritabani()
    loglar = []
    tur = {"n": 0}
    uyumalar = []

    def cekici(yapi, log=None):
        tur["n"] += 1
        if tur["n"] == 1:
            raise ConnectionError("overpass erisilemedi")
        return _cekici(yapi, log)

    def uyustur(sn):
        assert sn >= 600, f"tarama araligi cok kisa: {sn}sn"
        uyumalar.append(sn)
        if len(uyumalar) >= 2:
            raise KeyboardInterrupt

    try:
        try:
            a.aday_tarama_dongusu(lambda: _baglan(yol), _yapi(ADAY_ARALIK_DK="180",
                                                               ADAY_TEKRAR_DK="10"),
                                  loglar.append, cekici, uyustur)
        except KeyboardInterrupt:
            pass
        assert any("ADAY HATA" in s for s in loglar), loglar
        # Boşa giden tur 3 saat beklemez: kisa tekrar, iyi tur tam aralik.
        assert uyumalar == [600, 180 * 60], uyumalar
        # Ilk tur duus diye dongu olmedi: ikinci tur havuzu doldurdu.
        assert len(_hepsi(yol)) == 3, _hepsi(yol)
    finally:
        os.unlink(yol)


def test_dongu_bos_kaynakta_kisa_tekrara_duser():
    """Aynalar hata-firlatmadan bos donerse (Overpass yogunlugu) 3 saat beklenmez."""
    yol = _veritabani()
    loglar = []
    uyumalar = []
    tur = {"n": 0}

    def cekici(yapi, log=None):
        tur["n"] += 1
        if tur["n"] == 1:
            return [], ""  # hicbir sunucu yanit vermedi
        return _cekici(yapi, log)

    def uyustur(sn):
        uyumalar.append(sn)
        if len(uyumalar) >= 2:
            raise KeyboardInterrupt

    try:
        try:
            a.aday_tarama_dongusu(lambda: _baglan(yol), _yapi(ADAY_ARALIK_DK="180",
                                                              ADAY_TEKRAR_DK="10"),
                                  loglar.append, cekici, uyustur)
        except KeyboardInterrupt:
            pass
        assert uyumalar == [600, 180 * 60], uyumalar
        assert any("kaynaklardan firma alinamadi" in s for s in loglar), loglar
        assert len(_hepsi(yol)) == 3, _hepsi(yol)
    finally:
        os.unlink(yol)


def test_aday_tarama_kapali_iken_hicbir_sey_yapmaz():
    yol = _veritabani()
    loglar = []
    cagrilan = []

    def cekici(yapi, log=None):
        cagrilan.append(1)
        return [], ""

    try:
        a.aday_tarama_dongusu(lambda: _baglan(yol), _yapi(ADAY_TARAMA="0"), loglar.append,
                              cekici, lambda sn: None)
        assert cagrilan == [] and _hepsi(yol) == []
        assert any("KAPALI" in s for s in loglar), loglar
    finally:
        os.unlink(yol)


def test_operatorun_kendi_listesi_csv_den_aday_okunur():
    fd, csv_yol = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    with open(csv_yol, "w", encoding="utf-8") as fh:
        fh.write("isletme,telefon,adres\n")
        fh.write("Kahve Duraadi,0530 000 00 00,\"Ataturk Cad. No:12, Kusadasi\"\n")
        fh.write(",5321112233,Sokak 1\n")            # isimsiz -> atlanır
        fh.write("Farsan Firma,+44 1234 567890,Londra\n")
    yol = _veritabani()
    try:
        adaylar = a.csv_adaylari(csv_yol)
        assert [x["isletme"] for x in adaylar] == ["Kahve Duraadi", "Farsan Firma"]
        conn = _baglan(yol)
        try:
            ozet = a.adaylari_ala(conn, adaylar)
        finally:
            conn.close()
        assert ozet["eklenen"] == 2, ozet
        satirlar = _hepsi(yol)
        assert [s["telefon"] for s in satirlar] == ["0530 000 00 00", "+44 1234 567890"]
        assert all(s["izin"] == 0 and s["durum"] == a.ADAY_DURUM for s in satirlar)
        assert a.telefon_kanonik("+44 1234 567890") == "441234567890", "yurt disi 90'a cevrilmez"
    finally:
        os.unlink(csv_yol); os.unlink(yol)


def test_havuz_ozeti_panel_icin_sayilari_verir():
    yol = _veritabani()
    _tarayal(yol)
    conn = _baglan(yol)
    try:
        ozet = a.havuz_durumu(conn)
        assert ozet["toplam"] == 3 and ozet["izin_verilmis"] == 0
        assert ozet["telefonlu"] == 2 and ozet["adresli"] == 2
        assert "OpenStreetMap" in ozet["atıf"]
        assert ozet["ozet"]["kaynak"].startswith("https://overpass.example")
        conn.execute("UPDATE esnaflar SET izin=1 WHERE isletme='Zeytin Cafe'")
        conn.commit()
        assert a.havuz_durumu(conn)["izin_verilmis"] == 1
    finally:
        conn.close(); os.unlink(yol)


# ---------------------------------------------------------------------------
# KARO (TILE) TARAMASI — il geneli ölçekleme, ağ enjeksiyonla taklit edilir
# ---------------------------------------------------------------------------
_KARO_ENV = {"ADAY_BOLGE_BBOX": "37.80,27.20,37.84,27.28", "ADAY_TILE_KM": "2.0",
             "ADAY_KARO_BEKLEME_SN": "0"}

_CEVAP_GEO = {"elements": [
    {"type": "node", "id": 10, "lat": 37.8566, "lon": 27.2622, "tags": {
        "name": "Kroki Kitap", "phone": "+90 530 222 33 44", "addr:street": "Inonu Blv.",
        "addr:district": "Kusadasi", "addr:quarter": "Saricatlak"}},
    {"type": "way", "id": 11, "center": {"lat": 37.8601, "lon": 27.2701},
     "tags": {"name": "Etiketsiz Firin"}},
]}


class _Sunucu:
    """ac(url, veri, timeout) taklidi: idari sorguya bbox, POI sorgusuna bir firma."""

    def __init__(self, bolge_bbox=None):
        self.bolge_bbox = bolge_bbox
        self.admin = []
        self.poi_karolar = []
        self._sayac = 0

    def __call__(self, url, veri, timeout):
        if "out bb" in veri:
            self.admin.append(veri)
            if not self.bolge_bbox:
                return {"elements": []}
            minlat, minlon, maxlat, maxlon = self.bolge_bbox
            return {"elements": [{"type": "relation", "id": 1, "bounds": {
                "minlat": minlat, "minlon": minlon, "maxlat": maxlat, "maxlon": maxlon}}]}
        self.poi_karolar.append(re.search(r"\(([0-9.,\- ]+)\)", veri).group(1))
        self._sayac += 1   # karolar listesi testte temizlense de numara tekrarı yok
        return {"elements": [{"type": "node", "id": 900 + self._sayac,
                              "lat": 37.81, "lon": 27.21,
                              "tags": {"name": f"Firma {self._sayac}",
                                       "phone": f"0530 100 {self._sayac:04d}"}}]}


def _karo_yapi(**extra):
    env = dict(_KARO_ENV)
    env.update(extra)
    return _yapi(**env)


def test_karo_bboxlari_kutuyu_bosluk_birakmadan_doldurur():
    kutu = (37.80, 27.20, 37.84, 27.28)
    karolar = [tuple(float(x) for x in k.split(",")) for k in a.karo_bboxlari(kutu, 2.0)]
    assert len(karolar) > 4, karolar
    assert karolar[0][:2] == (37.80, 27.20), "ilk karo kutunun sol-alt köşesinden başlar"
    seritler = {}
    for minlat, minlon, maxlat, maxlon in karolar:
        seritler.setdefault((minlat, maxlat), []).append((minlon, maxlon))
    sicak = sorted(seritler)
    assert abs(sicak[0][0] - 37.80) < 1e-9 and abs(sicak[-1][1] - 37.84) < 1e-9
    for (_, alt), (ust, _) in zip(sicak, sicak[1:]):
        assert abs(ust - alt) < 1e-9, "şeritler arasında taranmamış bant var"
    for araliklar in seritler.values():
        araliklar.sort()
        assert abs(araliklar[0][0] - 27.20) < 1e-9 and abs(araliklar[-1][1] - 27.28) < 1e-9
        for (_, son), (bas, _) in zip(araliklar, araliklar[1:]):
            assert abs(bas - son) < 1e-9, "karo zincirinde boşluk var"
    # ~2 km kenar: enlem şeridi 2/111.32° (son şerit kutuya kırpılır)
    for alt, ust in sicak:
        if abs(ust - 37.84) > 1e-9:
            assert abs((ust - alt) * a._KM_LAT - 2.0) < 0.02


def test_karo_butcesi_kadar_istek_atilir_ve_imlecin_karosu_tekrarlanmaz():
    yapi = _karo_yapi(ADAY_TUR_KARO_AZAMI="2")
    sunucu = _Sunucu()
    bir, kaynak = a.osm_cek(yapi, log=lambda mesaj: None, ac=sunucu)
    assert len(bir) == 2 and yapi.karo_imleci == 2, (bir, yapi.karo_imleci)
    assert sunucu.admin == [], "bbox elle verildi: idari sınır sorgusu boşa istek"
    assert kaynak.startswith("https://overpass-api.de"), kaynak
    assert yapi.son_kapsama["mod"] == "KARO" and yapi.son_kapsama["karo_islenen"] == 2
    beklenti = a.karo_bboxlari((37.80, 27.20, 37.84, 27.28), 2.0)
    assert sunucu.poi_karolar == beklenti[:2]
    sunucu.poi_karolar.clear()
    a.osm_cek(yapi, log=lambda mesaj: None, ac=sunucu)
    assert sunucu.poi_karolar == beklenti[2:4], "imleç kaldığı yerden devam etmedi"


def test_imlec_veritabani_ozetinden_devam_eder_servis_yeniden_basaalsa():
    yol = _veritabani()
    sunucu = _Sunucu()
    cekici = lambda yapi, log=None: a.osm_cek(yapi, log, ac=sunucu)
    try:
        ozet = a.tarama_calistir(lambda: _baglan(yol), _karo_yapi(ADAY_TUR_KARO_AZAMI="2"),
                                 log=lambda mesaj: None, cekici=cekici)
        assert ozet["eklenen"] == 2 and ozet["karo_imleci"] == 2, ozet
        assert ozet["kapsama"]["mod"] == "KARO"
        beklenti = a.karo_bboxlari((37.80, 27.20, 37.84, 27.28), 2.0)
        sunucu.poi_karolar.clear()
        # Yeni nesne = yeniden başlayan servis: bellekteki imleç sıfır, DB'deki 2.
        ozet2 = a.tarama_calistir(lambda: _baglan(yol), _karo_yapi(ADAY_TUR_KARO_AZAMI="2"),
                                  log=lambda mesaj: None, cekici=cekici)
        assert sunucu.poi_karolar == beklenti[2:4], sunucu.poi_karolar
        assert ozet2["karo_imleci"] == 4 and ozet2["eklenen"] == 2, ozet2
        assert len(_hepsi(yol)) == 4 and all(s["izin"] == 0 for s in _hepsi(yol))
    finally:
        os.unlink(yol)


def test_karo_butceti_asilirsa_hic_bir_POI_istegi_atilmaz():
    yapi = _karo_yapi(ADAY_KARO_AZAMI="3", ADAY_TUR_KARO_AZAMI="1")
    sunucu = _Sunucu()
    loglar = []
    adaylar, kaynak = a.osm_cek(yapi, log=loglar.append, ac=sunucu)
    assert adaylar == [] and kaynak == "", "bütçe aşımı kısmi taramayla geçilmez"
    assert sunucu.poi_karolar == [] and yapi.son_kapsama["mod"] == "RED"
    assert any("ADAY_KARO_AZAMI" in s for s in loglar), loglar


def test_il_siniri_okunamazsa_tek_kutuya_duser_ve_bunu_sesser():
    yapi = _yapi(ADAY_BOLGE="Aydin", ADAY_KARO_BEKLEME_SN="0")
    sunucu = _Sunucu(bolge_bbox=None)   # her ayna boş/idari sınır yok
    loglar = []
    adaylar, _ = a.osm_cek(yapi, log=loglar.append, ac=sunucu)
    assert len(sunucu.admin) == len(yapi.url), "tüm aynalar denendikten sonra vazgeçilmeli"
    assert yapi.son_kapsama["mod"] == "TEK_KUTU" and len(adaylar) == 1
    assert any("tek kutuya" in s for s in loglar), loglar


def test_il_adi_gectersizse_idari_sorguya_hic_gidilmez():
    yapi = _yapi(ADAY_BOLGE='Aydin"; out; ', ADAY_KARO_BEKLEME_SN="0")
    sunucu = _Sunucu()
    adaylar, _ = a.osm_cek(yapi, log=lambda mesaj: None, ac=sunucu)
    assert sunucu.admin == [], "etiket enjeksiyonu denenen sorgu olmamalı"
    assert yapi.son_kapsama["mod"] == "TEK_KUTU" and len(adaylar) == 1


def test_karo_taramasi_kapali_iken_eski_tek_kutu_davranisi_surer():
    yapi = _yapi(ADAY_KARO_TARAMA="0")
    sunucu = _Sunucu()
    adaylar, _ = a.osm_cek(yapi, log=lambda mesaj: None, ac=sunucu)
    assert sunucu.admin == [] and sunucu.poi_karolar == [yapi.bbox]
    assert yapi.son_kapsama["mod"] == "TEK_KUTU" and len(adaylar) == 1


def test_geo_etiketleri_oldugu_gibi_yazilir_etiketi_yok_uydurulmaz():
    adaylar = a.osm_adaylari(_CEVAP_GEO)
    assert adaylar[0]["ilce"] == "Kusadasi" and adaylar[0]["mahalle"] == "Saricatlak"
    assert adaylar[0]["enlem"] == 37.8566 and adaylar[0]["boylam"] == 27.2622
    assert adaylar[1]["ilce"] is None and adaylar[1]["mahalle"] is None, "tahmin yok"
    assert adaylar[1]["enlem"] == 37.8601, "way için out center koordinatı okunmalı"
    assert adaylar[1]["kaynak"] == "OSM:way/11"


def test_ilce_mahalle_filtresi_yalnizca_esnaf_satirlarindan_suzulur():
    yol = _veritabani()
    conn = _baglan(yol)
    try:
        a.adaylari_ala(conn, a.osm_adaylari(_CEVAP_GEO) + a.osm_adaylari(_CEVAP))
        dagilim = {(d["ilce"], d["mahalle"]): d for d in a.bolge_dagilimi(conn)}
        assert dagilim[("Kusadasi", "Saricatlak")]["aday"] == 1, dagilim
        assert dagilim[(None, None)]["aday"] == 4, "etiketsiz kayıt 'biliniyor' sayılmaz"
        gorunen = a.havuz_durumu(conn, mahalle="Saricatlak")["kayitlar"]
        assert [k["isletme"] for k in gorunen] == ["Kroki Kitap"], gorunen
        assert gorunen[0]["kaynak"].startswith("OSM:node/10") and gorunen[0]["enlem"]
        assert a.havuz_durumu(conn, ilce="kusadasi")["toplam"] == 1, "harf büyüklüğü tolere"
        assert a.havuz_durumu(conn, ilce="Izmir")["toplam"] == 0
        assert a.havuz_durumu(conn)["mahalleli"] == 1
        # Filtre hiçbir zaman gönderim sırası üretmez: motor hâlâ kimseyi seçmez.
        assert _uygunlar(yol) == []
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
