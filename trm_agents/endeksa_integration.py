# -*- coding: utf-8 -*-
"""Endeksa entegrasyonu — FAIL-CLOSED.

Eski hâli hiçbir HTTP isteği atmadan beş "premium ilçe", sahte ortalama konut
fiyatları, `luxury_index` ve mahalle bazlı tüketici profili (yaş aralığı
35-55, hane geliri 500000+, "wealthy_retirees") uyduruyordu. Endeksa ticari
bir veri sağlayıcısıdır; lisanslı besleme olmadan burada tek bir sayı bile
üretilmez. Tüketici/refah profillemesi bilerek kaldırılmıştır.

Anahtar varlığı yalnızca kontrol edilir; değer okunmaz ve yazılmaz. Anahtar
olsa bile doğrulanmış bir uç nokta yapılandırılmadıkça durum değişmez:
`not_configured`.
"""

import logging
import os
from typing import Dict, List

logger = logging.getLogger(__name__)

NOT_CONFIGURED = "not_configured"
ANAHTAR_ADAYLARI = ("ENDEKSA_API_TOKEN", "ENDEKSA_API_KEY")


def anahtar_var_mi(environ=None) -> bool:
    e = os.environ if environ is None else environ
    return any(str(e.get(ad) or "").strip() for ad in ANAHTAR_ADAYLARI)


class EndeksaIntegration:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or ""
        self.base_url = "https://api.endeksa.com.tr/v1"
        self.durum = NOT_CONFIGURED

    def _sebep(self) -> str:
        if not (self.api_key or anahtar_var_mi()):
            return "lisanslı Endeksa anahtarı yok (ENDEKSA_API_TOKEN beklenir)"
        return "anahtar var ama doğrulanmış Endeksa uç noktası yapılandırılmadı"

    def _red(self, konu: str) -> Dict[str, object]:
        logger.warning(f"Endeksa -> not_configured ({konu})")
        return {"durum": NOT_CONFIGURED, "konu": konu, "sebep": self._sebep(), "veri": None}

    def get_premium_districts(self, city: str = "Istanbul") -> List[Dict]:
        # Boş liste = veri yok; "bölge var ama skoru yok" demek yanıltıcı olurdu.
        self._red(f"premium_bolgeler ({city})")
        return []

    def get_high_value_locations(self, min_price: int = 0) -> List[Dict]:
        self._red("degerli_konut_listesi")
        return []

    def get_elite_audience_profile(self, district: str = "") -> Dict:
        # Alım gücüne göre tüketici profillemesi: üretilmez, reddedilir.
        return self._red(f"elit_kitle_profili ({district})")

    def analyze_luxury_product_fit(self, product: Dict = None,
                                   target_districts: List[str] = None) -> Dict:
        return self._red("luks_urun_uyumu")


if __name__ == "__main__":
    servis = EndeksaIntegration()
    print(servis.get_premium_districts("İstanbul"))
    print(servis.analyze_luxury_product_fit({}, []))
