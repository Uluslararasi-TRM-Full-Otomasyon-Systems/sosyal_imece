import json
from datetime import datetime

def analyze_geo_target(region_name: str, target_demographic: str = "55_plus_and_general"):
    """
    Coğrafi bölge/lokasyon bazlı lojistik, sosyal yayılım ve 
    afiliyet/imece potansiyel skorlaması yapar.
    """
    base_scores = {
        "ankara": {"logistics_score": 92, "community_density": 88, "recommended_hub": "Ankara Merkez İmece Hub"},
        "istanbul": {"logistics_score": 95, "community_density": 94, "recommended_hub": "Marmara Bölge Dağıtım"},
        "izmir": {"logistics_score": 90, "community_density": 85, "recommended_hub": "Ege Sosyal İmece Üssü"},
        "kuşadası": {"logistics_score": 88, "community_density": 91, "recommended_hub": "Aydın-Ege Sahil İmece"}
    }
    
    clean_key = region_name.lower().strip()
    geo_data = base_scores.get(clean_key, {
        "logistics_score": 80,
        "community_density": 82,
        "recommended_hub": f"{region_name.title()} Otonom İmece Noktası"
    })

    result = {
        "timestamp": datetime.now().isoformat(),
        "query_region": region_name,
        "demographic_target": target_demographic,
        "metrics": geo_data,
        "status": "GEO_PROFILED"
    }

    log_file = "geospy_logs.json"
    history = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            history = json.load(f)
    except FileNotFoundError:
        pass
    history.append(result)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return result

if __name__ == "__main__":
    print("--- GeoSpy Entegrasyon Testi ---")
    res = analyze_geo_target(region_name="Kuşadası", target_demographic="55_plus_kıdemli")
    print(json.dumps(res, ensure_ascii=False, indent=2))
