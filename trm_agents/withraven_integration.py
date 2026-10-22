# -*- coding: utf-8 -*-
"""WithRaven entegrasyonu — FAIL-CLOSED.

Eski hâli hiçbir modele ya da servise istek atmadan `confidence_score: 0.87`,
`conversion_probability: 0.73`, `niche_confidence: 0.78`, "impulse_buyers:
0.35" gibi uydurma çıkarımlar ve bunlara dayalı tüketici segmentasyonu
üretiyordu. Gerçek bir lisanslı uç nokta yapılandırılmadıkça bu modül tek bir
sayı ya da öneri üretmez; her yöntem `durum='not_configured'` döner.

Tüketici davranış/demografi segmentasyonu bilerek kaldırılmıştır: TRM'nin
meşru hedefi, OSM ticari POI verisinden bulunup operatör tarafından onaylanmış
esnaf kayıtlarıdır (bkz. aday_havuzu.py).
"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

NOT_CONFIGURED = "not_configured"
ANAHTAR_ADAYLARI = ("WITHRAVEN_API_TOKEN", "WITHRAVEN_API_KEY")


def anahtar_var_mi(environ=None) -> bool:
    e = os.environ if environ is None else environ
    return any(str(e.get(ad) or "").strip() for ad in ANAHTAR_ADAYLARI)


class WithRavenIntegration:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""
        self.durum = NOT_CONFIGURED
        self.model_version = None

    def _sebep(self) -> str:
        if not (self.api_key or anahtar_var_mi()):
            return "lisanslı WithRaven anahtarı yok (WITHRAVEN_API_TOKEN beklenir)"
        return "anahtar var ama doğrulanmış WithRaven uç noktası yapılandırılmadı"

    def _red(self, konu: str) -> Dict[str, Any]:
        logger.warning(f"WithRaven -> not_configured ({konu})")
        return {"durum": NOT_CONFIGURED, "konu": konu, "sebep": self._sebep(),
                "veri": None}

    def process_geographic_data(self, geo_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._red("cografi_veri_isleme")

    def analyze_behavioral_patterns(self, behavioral_data: Dict[str, Any]) -> Dict[str, Any]:
        # Davranışsal kitle segmentasyonu: üretilmez, reddedilir.
        return self._red("davranisal_analiz")

    def generate_decision_support(self, combined_data: Dict[str, Any]) -> Dict[str, Any]:
        red = self._red("karar_destek")
        red["girdi_ozeti"] = {
            "cografi": bool((combined_data or {}).get("geographic")),
            "davranisal": bool((combined_data or {}).get("behavioral")),
            "pazar": bool((combined_data or {}).get("market")),
        }
        return red

    def integrate_dnp_data(self, dnp_data: Dict[str, Any]) -> Dict[str, Any]:
        red = self._red("dnp_entegrasyonu")
        red["girdi_nis"] = (dnp_data or {}).get("primary_niche", "general")
        return red


if __name__ == "__main__":
    servis = WithRavenIntegration()
    print(servis.process_geographic_data({}))
    print(servis.analyze_behavioral_patterns({}))
