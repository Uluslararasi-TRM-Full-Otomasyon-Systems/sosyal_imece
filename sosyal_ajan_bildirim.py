import json
from datetime import datetime

def ajan_duyuru_uret(closed_loop_rapor: dict):
    sepet = closed_loop_rapor["sepet_islem"]
    dagitim = closed_loop_rapor["dagitim_ozet"]
    
    duyuru_metni = f"""
🌟 **TRM Sosyal İmece Anlık Otonom Raporu** ({datetime.now().strftime('%Y-%m-%d %H:%M')})
--------------------------------------------------
🛒 **Sepet Eşleşme:** {sepet['sepet_id']} | Tutar: {sepet['sepet_tutar_tl']} TL
💎 **İmece Havuz Katkısı:** {sepet['imece_havuz_aktarim_tl']} TL
👤 **Üye Cüzdan Net:** {sepet['net_uye_cuzdan_tl']} TL
--------------------------------------------------
🏛️ **Adil Dağıtım Özeti:**
- Toplam Dağıtılan Fon: {dagitim['toplam_dagitilan_fon_tl']:,.2f} TL
- Toplam Üye: {dagitim['n_toplam_uye']} kişi
- 55+ Kıdemli Zenginlik Payı Alan: {dagitim['n_55_plus_kıdemli']} kişi
--------------------------------------------------
✨ *Birlikte üretiyor, 55+ kıdemli refah payıyla hakça bölüşüyoruz!*
"""

    bildirim_kaydi = {
        "timestamp": datetime.now().isoformat(),
        "kanal": ["telegram_channel", "whatsapp_broadcast", "trm_otonom_feed"],
        "icerik": duyuru_metni.strip(),
        "durum": "HAZIR_VE_YAYINLANABILIR"
    }

    log_dosyasi = "sosyal_duyuru_loglari.json"
    mevcut = []
    try:
        with open(log_dosyasi, "r", encoding="utf-8") as f:
            mevcut = json.load(f)
    except FileNotFoundError:
        pass

    mevcut.append(bildirim_kaydi)
    with open(log_dosyasi, "w", encoding="utf-8") as f:
        json.dump(mevcut, f, ensure_ascii=False, indent=2)

    return bildirim_kaydi

if __name__ == "__main__":
    from trm_master_pipeline import master_siparis_ve_havuz_dongusu
    siparis = {"sepet_id": "TRM-LIVE-2026-0922", "uye_id": "APL-55-ALTIN", "tutar": 5000.0, "komisyon_orani": 0.20}
    uyeler = [
        {"id": "APL-55-ALTIN", "ad": "Mehmet Fahri", "yas": 63, "durum": "onayli"},
        {"id": "APL-02", "ad": "Ayşe Teyze", "yas": 60, "durum": "onayli"},
        {"id": "APL-03", "ad": "Can Genç", "yas": 28, "durum": "onayli"},
        {"id": "APL-04", "ad": "Zeynep", "yas": 42, "durum": "onayli"}
    ]
    loop_res = master_siparis_ve_havuz_dongusu(siparis, uyeler)
    res = ajan_duyuru_uret(loop_res)
    print("--- Sosyal Ajan Bildirim Çıktısı ---")
    print(res["icerik"])
