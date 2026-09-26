import json
from datetime import datetime

def profile_dynamic_niche(niche_category: str, avg_basket_tl: float, target_age_bracket: str = "all"):
    """
    trendurunlermarket.com kataloğu için dinamik niş kârlılık,
    komisyon verimliliği ve imece havuz katkı öngörüsü çıkarır.
    """
    margin_multipliers = {
        "sağlık_yaşam": 0.22,
        "organik_gıda": 0.18,
        "ev_dekorasyon": 0.25,
        "teknoloji_aksesuar": 0.20
    }
    
    key = niche_category.lower().replace(" ", "_")
    komisyon_orani = margin_multipliers.get(key, 0.19)
    estimated_monthly_volume = 1200 #simüle edilen aylık sepet hacmi
    est_brut_revenue = avg_basket_tl * estimated_monthly_volume * komisyon_orani
    imece_pool_contribution = est_brut_revenue * 0.30

    profil_raporu = {
        "timestamp": datetime.now().isoformat(),
        "niche_category": niche_category,
        "target_age_bracket": target_age_bracket,
        "komisyon_orani": komisyon_orani,
        "tahmini_aylik_brut_komisyon_tl": round(est_brut_revenue, 2),
        "tahmini_imece_havuz_katkisi_tl": round(imece_pool_contribution, 2),
        "skor_durumu": "OPTIMAL_NIŞ_ONAYLANDI"
    }

    log_file = "niche_profiler_logs.json"
    history = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            history = json.load(f)
    except FileNotFoundError:
        pass
    history.append(profil_raporu)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return profil_raporu

if __name__ == "__main__":
    print("--- Dinamik Niş Profilleyici Testi ---")
    res = profile_dynamic_niche(
        niche_category="sağlık_yaşam",
        avg_basket_tl=1800.0,
        target_age_bracket="55_plus_odakli"
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
