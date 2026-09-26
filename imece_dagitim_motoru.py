import json
from datetime import datetime

def hesapla_ve_dagit(toplam_havuz_tl: float, uyeler: list):
    """
    Kural:
    1. Sistemdeki herkese imece payı + %20 refah payı dağıtılır.
    2. Ardından 55 yaş ve üzeri kişilere ayrıca sadece imece zenginlik payı bölüştürülür.
    
    uyeler yapısı: [{ 'id': '...', 'ad': '...', 'yas': 58, 'durum': 'onayli' }, ...]
    """
    aktif_uyeler = [u for u in uyeler if u.get('durum') == 'onayli']
    n_toplam = len(aktif_uyeler)
    
    if n_toplam == 0:
        return {"hata": "Aktif onaylı üye bulunamadı."}

    # Havuzun %80'i temel imece + refah payına, %20'si 55+ zenginlik payına ayrılsın (veya esnek oran)
    # Temel + Refah Payı Havuzu: Toplamın %80'i
    temel_refah_toplam = toplam_havuz_tl * 0.80
    # Zenginlik Payı Havuzu (55+): Toplamın %20'si
    zenginlik_toplam = toplam_havuz_tl * 0.20

    # Herkese eşit temel imece + %20 refah payı bileşeni
    kisi_basi_temel_refah = temel_refah_toplam / n_toplam

    # 55 yaş ve üzeri üyeler
    kıdemli_55_plus = [u for u in aktif_uyeler if u.get('yas', 0) >= 55]
    n_kıdemli = len(kıdemli_55_plus)
    kisi_basi_zenginlik = (zenginlik_toplam / n_kıdemli) if n_kıdemli > 0 else 0.0

    hesap_dokumu = []
    for u in aktif_uyeler:
        yas = u.get('yas', 30)
        temel_pay = kisi_basi_temel_refah
        zenginlik_pay = kisi_basi_zenginlik if yas >= 55 else 0.0
        toplam_aktarim = temel_pay + zenginlik_pay
        
        hesap_dokumu.append({
            "uye_id": u.get('id'),
            "ad": u.get('ad', 'Ortak'),
            "yas": yas,
            "temel_plus_refah_payi": round(temel_pay, 2),
            "zenginlik_payi_55_plus": round(zenginlik_pay, 2),
            "toplam_hesaba_aktarilan": round(toplam_aktarim, 2),
            "kategori": "55+ Kıdemli + Zenginlik Dahil" if yas >= 55 else "Standart İmece + Refah"
        })

    rapor = {
        "timestamp": datetime.now().isoformat(),
        "toplam_dagitilan_havuz_tl": toplam_havuz_tl,
        "n_toplam_uye": n_toplam,
        "n_55_plus_uye": n_kıdemli,
        "detaylar": hesap_dokumu
    }

    try:
        with open("dagitim_audit_log.json", "w", encoding="utf-8") as f:
            json.dump(rapor, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Dagıtım] Log yazma hatası: {e}")

    return rapor

if __name__ == "__main__":
    test_uyeler = [
        {"id": "APL-55-ALTIN", "ad": "Mehmet Fahri", "yas": 63, "durum": "onayli"},
        {"id": "APL-02", "ad": "Ayşe Teyze", "yas": 60, "durum": "onayli"},
        {"id": "APL-03", "ad": "Can Genç", "yas": 28, "durum": "onayli"},
        {"id": "APL-04", "ad": "Zeynep", "yas": 42, "durum": "onayli"}
    ]
    sonuc = hesapla_ve_dagit(100000.0, test_uyeler)
    print("Test Dağıtım Özeti:")
    print(f"Toplam Üye: {sonuc['n_toplam_uye']} | 55+ Üye: {sonuc['n_55_plus_uye']}")
    for d in sonuc['detaylar']:
        print(f" - {d['ad']} ({d['yas']} yaş) [{d['kategori']}]: Toplam Aktarım = {d['toplam_hesaba_aktarilan']} TL")
