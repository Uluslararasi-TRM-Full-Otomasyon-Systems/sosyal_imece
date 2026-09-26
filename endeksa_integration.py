import logging
from dataclasses import dataclass
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("EndeksaIntegration")

@dataclass
class EndeksaRegionMetrics:
    city: str
    district: str
    neighborhood: Optional[str]
    avg_sqm_price_try: float
    annual_rental_yield_pct: float
    amortization_years: float
    regional_wealth_index: float
    data_confidence_score: float

class EndeksaIntegration:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "mock_endeksa_trm_token_99"
        self.mock_db: Dict[str, Dict[str, float]] = {
            "istanbul_kadikoy": {"sqm": 85000.0, "yield": 5.2, "wealth_idx": 91.0},
            "ankara_cankaya": {"sqm": 54000.0, "yield": 6.0, "wealth_idx": 84.0},
            "aydin_kusadasi": {"sqm": 42000.0, "yield": 6.8, "wealth_idx": 88.0},
            "izmir_cesme": {"sqm": 95000.0, "yield": 4.5, "wealth_idx": 94.0},
        }

    def _normalize_key(self, city: str, district: str) -> str:
        c = city.lower().replace("ı", "i").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c").replace("ğ", "g")
        d = district.lower().replace("ı", "i").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c").replace("ğ", "g")
        return f"{c}_{d}"

    def fetch_region_valuation(self, city: str, district: str, neighborhood: Optional[str] = None) -> EndeksaRegionMetrics:
        key = self._normalize_key(city, district)
        logger.info(f"Endeksa veri sorgulanıyor -> Lokasyon: {city}/{district}/{neighborhood or 'Genel'}")
        if key in self.mock_db:
            data = self.mock_db[key]
            sqm, yd, w_idx = data["sqm"], data["yield"], data["wealth_idx"]
            amort = round(100.0 / yd, 1) if yd > 0 else 20.0
            confidence = 0.92
        else:
            sqm, yd, w_idx, amort, confidence = 35000.0, 6.5, 75.0, 15.4, 0.74
            logger.warning(f"Exact match bulunamadı ({key}), makro bölge sentetik modeli uygulandı.")
        return EndeksaRegionMetrics(city, district, neighborhood, sqm, yd, amort, w_idx, confidence)

    def compute_sosyal_imece_asset_multiplier(self, metrics: EndeksaRegionMetrics) -> float:
        base_multiplier = 1.0
        wealth_bonus = (metrics.regional_wealth_index - 50.0) * 0.005
        yield_bonus = (metrics.annual_rental_yield_pct - 5.0) * 0.02
        return round(max(0.85, min(1.35, base_multiplier + wealth_bonus + yield_bonus)), 4)

if __name__ == "__main__":
    service = EndeksaIntegration()
    res = service.fetch_region_valuation("Aydın", "Kuşadası", "İnönü Blv.")
    mult = service.compute_sosyal_imece_asset_multiplier(res)
    print("Endeksa Test:", res)
    print("Sosyal İmece Varlık Çarpanı:", mult)
