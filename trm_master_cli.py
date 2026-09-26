import json
from trm_master_pipeline import master_siparis_ve_havuz_dongusu
from sosyal_ajan_bildirim import ajan_duyuru_uret
from geospy_integration import analyze_geo_target
from dynamic_niche_profiler import profile_dynamic_niche
from endeksa_integration import EndeksaIntegration
from hoodmaps_integration import HoodmapsIntegration

def calistir_tam_ekosistem_simulasyonu():
    print("==================================================")
    print("🌟 TRM FULL OTOMASYON & SOSYAL İMECE MASTER KONSOL")
    print("==================================================")

    # 1. Lokasyon & Varlık Katmanı
    geo_res = analyze_geo_target("Kuşadası", "55_plus_kıdemli")
    endeksa_svc = EndeksaIntegration()
    end_res = endeksa_svc.fetch_region_valuation("Aydın", "Kuşadası", "İnönü Blv.")
    end_mult = endeksa_svc.compute_sosyal_imece_asset_multiplier(end_res)
    
    hood_svc = HoodmapsIntegration()
    hood_profile = hood_svc.analyze_neighborhood_identity("Aydın", "Kuşadası", "İnönü")
    hood_fit = hood_svc.evaluate_sosyal_imece_fit(hood_profile)

    # 2. Niş & Komisyon Katmanı
    niche_res = profile_dynamic_niche("sağlık_yaşam", 2500.0, "55_plus_odakli")

    # 3. Sepet & 55+ Zenginlik / Refah Havuz Dağıtımı
    siparis = {
        "sepet_id": "TRM-MASTER-9999",
        "uye_id": "APL-55-ALTIN",
        "tutar": 7500.0 * hood_fit["distribution_velocity_multiplier"],
        "komisyon_orani": 0.22
    }
    uyeler = [
        {"id": "APL-55-ALTIN", "ad": "Mehmet Fahri", "yas": 63, "durum": "onayli"},
        {"id": "APL-02", "ad": "Ayşe Teyze", "yas": 60, "durum": "onayli"},
        {"id": "APL-03", "ad": "Can Genç", "yas": 28, "durum": "onayli"},
        {"id": "APL-04", "ad": "Zeynep", "yas": 42, "durum": "onayli"}
    ]
    loop_res = master_siparis_ve_havuz_dongusu(siparis, uyeler)

    # 4. Sosyal Ajan Duyurusu
    duyuru_res = ajan_duyuru_uret(loop_res)

    master_rapor = {
        "lokasyon_analizi": geo_res,
        "gayrimenkul_varlik_carpan": end_mult,
        "hoodmaps_demografi_fit": hood_fit,
        "nis_profil": niche_res,
        "kapali_cevril_islem": loop_res,
        "sosyal_duyuru": duyuru_res
    }

    log_file = "master_komuta_log.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(master_rapor, f, ensure_ascii=False, indent=2)

    print("✅ Master Ekosistem Senkronizasyonu Tamamlandı!")
    print(f"📍 Bölge Varlık Çarpanı: {end_mult} | İmece Fit Skoru: {hood_fit['imece_demographic_fit_score']}")
    print(f"💎 Net Cüzdan & Havuz Aktarımı: {loop_res['sepet_islem']['net_uye_cuzdan_tl']} TL üye / {loop_res['sepet_islem']['imece_havuz_aktarim_tl']} TL imece")
    print(f"📢 Sosyal Duyuru Kuyruğa Atıldı ({len(duyuru_res['kanal'])} kanal).")

if __name__ == "__main__":
    calistir_tam_ekosistem_simulasyonu()
