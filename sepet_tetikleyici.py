import json
from datetime import datetime

def sepet_isleme_tetikle(sepet_id: str, uye_id: str, sepet_tutar_tl: float, afiliyet_komisyon_orani: float = 0.15):
    """
    trendurunlermarket.com / Afiliyet sepet hareketini yakalar,
    imece havuzuna ve üye refah/cüzdan hesabına işler.
    """
    brut_komisyon = sepet_tutar_tl * afiliyet_komisyon_orani
    imece_katki_orani = 0.30  # Komisyonun %30'u sosyal imece havuzuna aktarılır
    imece_fonu = brut_komisyon * imece_katki_orani
    net_uye_kazanci = brut_komisyon - imece_fonu

    kayit = {
        "timestamp": datetime.now().isoformat(),
        "sepet_id": sepet_id,
        "uye_id": uye_id,
        "sepet_tutar_tl": sepet_tutar_tl,
        "brut_komisyon_tl": round(brut_komisyon, 2),
        "imece_havuz_aktarim_tl": round(imece_fonu, 2),
        "net_uye_cuzdan_tl": round(net_uye_kazanci, 2),
        "durum": "ESLESTI_VE_AKTARILDI"
    }

    log_dosyasi = "sepet_tetikleme_loglari.json"
    mevcut_loglar = []
    try:
        with open(log_dosyasi, "r", encoding="utf-8") as f:
            mevcut_loglar = json.load(f)
    except FileNotFoundError:
        pass

    mevcut_loglar.append(kayit)
    with open(log_dosyasi, "w", encoding="utf-8") as f:
        json.dump(mevcut_loglar, f, ensure_ascii=False, indent=2)

    return kayit

if __name__ == "__main__":
    print("--- Sepet Eşleşme Tetikleyici Testi ---")
    res = sepet_isleme_tetikle(
        sepet_id="TRM-SEP-99881",
        uye_id="APL-55-ALTIN",
        sepet_tutar_tl=2500.0,
        afiliyet_komisyon_orani=0.18
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
