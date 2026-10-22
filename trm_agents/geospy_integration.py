# -*- coding: utf-8 -*-
"""GeoSpy entegrasyonu — FAIL-CLOSED.

Eski hâli `api.geospy.ai/v1` adresine tek bir istek atmadan İstanbul/Kadıköy
koordinatları, `confidence: 0.87`, sahte demografi (`population_density: high`)
ve altyapı yüzdeleri (`internet_penetration: 0.95`) uyduruyordu;
`analyze_geographic_relevance` ise okunan veriye bakmadan 0.7/0.5 skor
atıyordu. Bu sürüm hiçbir değer üretmez: doğrulanmış bir uç nokta ve lisanslı
anahtar olmadan her yöntem `durum='not_configured'` döner.

Anahtar varlığı yalnızca kontrol edilir; değeri okunmaz ve yazılmaz.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

NOT_CONFIGURED = "not_configured"
ANAHTAR_ADAYLARI = ("GEOSPYPY_API_TOKEN", "GEOSPY_API_TOKEN", "GEOSPY_API_KEY")


def anahtar_var_mi(environ=None) -> bool:
    e = os.environ if environ is None else environ
    return any(str(e.get(ad) or "").strip() for ad in ANAHTAR_ADAYLARI)


class GeoSpyIntegration:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""
        self.base_url = "https://api.geospy.ai/v1"
        self.durum = NOT_CONFIGURED

    def _sebep(self) -> str:
        if not (self.api_key or anahtar_var_mi()):
            return "lisanslı GeoSpy anahtarı yok (GEOSPY_API_TOKEN beklenir)"
        return "anahtar var ama doğrulanmış GeoSpy uç noktası yapılandırılmadı"

    def _red(self, konu: str) -> Dict[str, object]:
        logger.warning(f"GeoSpy -> not_configured ({konu})")
        return {"durum": NOT_CONFIGURED, "konu": konu, "sebep": self._sebep(),
                "veri": None}

    def analyze_image_location(self, image_data: bytes) -> Dict:
        # Görselden çıkarılan konum, gerçek bir model cevabı olmadan uydurulamaz.
        return self._red("gorsel_konum_analizi")

    def verify_location_claim(self, claimed_location: str,
                              image_data: bytes) -> Dict:
        # Doğrulama yapamıyorsak "doğrulanamadı" deriz; iddiayı ne kabul ne red.
        red = self._red(f"konum_iddiası ({claimed_location})")
        red["is_verified"] = None
        return red

    def get_location_intelligence(self, location: str) -> Dict:
        # Yaş/gelir/altyapı gibi tüketici profilleri bilerek üretilmez.
        return self._red(f"konum_istihbarati ({location})")

    def analyze_geographic_relevance(self, content: Dict,
                                     target_locations: List[str]) -> Dict:
        # Skor biçiminde anahtar (`overall_relevance` vb.) bile üretilmez:
        # kırmızı bir sayı olmaması, yeşil bir sayının yerini almamalı.
        red = self._red("cografik_uyumluluk")
        red["content"] = (content or {}).get("title", "unknown")
        red["target_locations"] = list(target_locations or [])
        return red

    def batch_verify_images(self,
                            image_location_pairs: List[Tuple[bytes, str]]) -> List[Dict]:
        return [self.verify_location_claim(konu, gorsel)
                for gorsel, konu in (image_location_pairs or [])]


if __name__ == "__main__":
    servis = GeoSpyIntegration()
    print(servis.get_location_intelligence("İstanbul"))
    print(servis.analyze_image_location(b""))
