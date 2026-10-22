# -*- coding: utf-8 -*-
"""Hoodmaps entegrasyonu — FAIL-CLOSED.

Eski hâli `api.hoodmaps.com/v1` adresine hiç istek atmadan yaş dağılımı, gelir
düzeyi, "target_score": 0.75 gibi uydurma değerler döndürüyordu; üstelik bu
değerler tüketici hedeflemesi için kullanılıyordu. Hoodmaps'in herkese açık
bir API'si yoktur, kazımak hizmet şartlarına aykırıdır.

Bu sürüm hiçbir veri üretmez: her yöntem `durum='not_configured'` döner ve
sebep olarak neyin eksik olduğunu söyler. Yaş/gelir/demografi alanları
bilerek kaldırıldı — TRM'nin meşru coğrafi filtresi OSM ticari POI verisi ve
operatörün onayladığı esnaf kayıtlarıdır (bkz. aday_havuzu.py).
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

NOT_CONFIGURED = "not_configured"
SEBEP = ("Hoodmaps API'si yok / kazımak hizmet şartlarına aykırı; "
         "uydurma demografi üretilmez")


def _red(konu: str, lokasyon: str = "") -> Dict[str, object]:
    logger.warning(f"Hoodmaps -> not_configured ({konu}: {lokasyon})")
    return {"durum": NOT_CONFIGURED, "konu": konu, "lokasyon": lokasyon,
            "sebep": SEBEP, "veri": None}


class HoodmapsIntegration:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or ""
        self.base_url = "https://api.hoodmaps.com/v1"
        self.durum = NOT_CONFIGURED
        self.sebep = SEBEP

    def get_neighborhood_demographics(self, location: str) -> Dict:
        return _red("mahalle_demografisi", location)

    def get_cultural_insights(self, location: str) -> Dict:
        return _red("kulturel_icgoru", location)

    def analyze_target_audience(self, location: str, product_category: str = "") -> Dict:
        # "hedef kitle" = tüketici hedeflemesi: bu modül bunu yapmaz.
        return _red("hedef_kitle_analizi", location)

    def analyze_luxury_targeting(self, city: str = "") -> Dict:
        return _red("luks_hedefleme", city)


if __name__ == "__main__":
    print(HoodmapsIntegration().analyze_target_audience("Istanbul", "electronics"))
