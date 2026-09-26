from sepet_tetikleyici import sepet_isleme_tetikle
from imece_dagitim_motoru import hesapla_ve_dagit
import json

def master_siparis_ve_havuz_dongusu(siparis_data: dict, tum_uyeler: list):
    # 1. Sepet / Afiliyet Komisyon Eşleşmesi
    sepet_res = sepet_isleme_tetikle(
        sepet_id=siparis_data["sepet_id"],
        uye_id=siparis_data["uye_id"],
        sepet_tutar_tl=siparis_data["tutar"],
        afiliyet_komisyon_orani=siparis_data.get("komisyon_orani", 0.20)
    )
    
    # 2. İmece havuzuna biriken katkıyı refah matrisine besle
    toplam_havuz_simulasyon = sepet_res["imece_havuz_aktarim_tl"] * 500  # Havuz ölçekleme
    dagitim_res = hesapla_ve_dagit(toplam_havuz_simulasyon, tum_uyeler)
    
    return {
        "status": "CLOSED_LOOP_SUCCESS",
        "sepet_islem": sepet_res,
        "dagitim_ozet": {
            "toplam_dagitilan_fon_tl": dagitim_res.get("toplam_dagitilan_havuz_tl"),
            "n_toplam_uye": dagitim_res.get("n_toplam_uye"),
            "n_55_plus_kıdemli": dagitim_res.get("n_55_plus_uye")
        }
    }

if __name__ == "__main__":
    print("--- TRM Kapalı Çevrim Master Pipeline Testi ---")
    ornek_siparis = {
        "sepet_id": "TRM-LIVE-2026-0922",
        "uye_id": "APL-55-ALTIN",
        "tutar": 5000.0,
        "komisyon_orani": 0.20
    }
    ornek_aktif_uyeler = [
        {"id": "APL-55-ALTIN", "ad": "Mehmet Fahri", "yas": 63, "durum": "onayli"},
        {"id": "APL-02", "ad": "Ayşe Teyze", "yas": 60, "durum": "onayli"},
        {"id": "APL-03", "ad": "Can Genç", "yas": 28, "durum": "onayli"},
        {"id": "APL-04", "ad": "Zeynep", "yas": 42, "durum": "onayli"}
    ]
    sonuc = master_siparis_ve_havuz_dongusu(ornek_siparis, ornek_aktif_uyeler)
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
