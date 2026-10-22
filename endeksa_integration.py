# -*- coding: utf-8 -*-
"""Endeksa entegrasyonu — FAIL-CLOSED.

Eskiden bu dosya `mock_endeksa_trm_token_99` ile dört sahte ilçe verisi tutuyor
ve eşleşmeyen her bölgeye sentetik değer (35.000 TL/m², %6,5 verim, 75 refah
skoru) üretiyordu. O sayılar hiçbir kaynaktan gelmiyordu; panelden bakınca
"analiz" gibi görünüp ticari karara karışabiliyorlardı. Bu sürümde:

  * lisanslı anahtar yoksa -> HİÇBİR sayı üretmez, durum `not_configured`;
  * anahtar olsa bile doğrulanmış bir uç nokta yoksa -> `not_configured`
    (uç nokta uydurmak, anahtarı çalıştırmak değil);
  * çarpan hesabı YALNIZCA `durum == "ok"` ile taşınmış metrikler üzerinde
    çalışır; sahte/eksik girdiyle çağrılırsa hesap yapılmaz, red döner.

Not: Endeksa ticari bir veri sağlayıcısıdır; veri alınacaksa bu bir lisans
anlaşmasına dayanmak zorundadır. Anahtar operatörden gelir (`.env` boş iskelet
olarak durur), bu modül anahtar değerini asla yazdırmaz.
"""

import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("EndeksaIntegration")

NOT_CONFIGURED = "not_configured"
OK = "ok"
ANAHTAR_ADAYLARI = ("ENDEKSA_API_TOKEN", "ENDEKSA_API_KEY")


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
    durum: str = OK


def anahtar_var_mi(environ=None) -> bool:
    """Anahtar DEĞERİ okunmaz; yalnızca var mı diye sorulur."""
    e = os.environ if environ is None else environ
    return any(str(e.get(ad) or "").strip() for ad in ANAHTAR_ADAYLARI)


def _red(sebep: str, city: str, district: str) -> Dict[str, object]:
    logger.warning(f"Endeksa -> {sebep} ({city}/{district})")
    return {"durum": NOT_CONFIGURED, "sebep": sebep, "city": city, "district": district,
            "metrik": None}


def fetch_region_valuation(city: str, district: str,
                           neighborhood: Optional[str] = None) -> Dict[str, object]:
    """Lisanslı besleme yoksa dürüst red; sayı uydurmaz.

    `metrik` alanı YALNIZCA doğrulanmış bir kaynak `durum='ok'` ile döner.
    """
    if not anahtar_var_mi():
        return _red("lisanslı Endeksa anahtarı yok (ENDEKSA_API_TOKEN)", city, district)
    return _red("anahtar var ama doğrulanmış Endeksa uç noktası yapılandırılmadı",
                city, district)


def compute_sosyal_imece_asset_multiplier(metrics) -> Dict[str, object]:
    """Varlık çarpanı; girdi doğrulanmış değilse hesaplanmaz (fail-closed)."""
    if isinstance(metrics, dict):
        durum = metrics.get("durum")
        metrik = metrics.get("metrik")
    else:
        durum = getattr(metrics, "durum", None)
        metrik = metrics
    if durum != OK or metrik is None or not isinstance(metrik, EndeksaRegionMetrics):
        return {"durum": NOT_CONFIGURED,
                "sebep": "çarpan yalnızca durum='ok' ile taşınan gerçek metrik üzerinde hesaplanır",
                "carpan": None}
    wealth_bonus = (metrik.regional_wealth_index - 50.0) * 0.005
    yield_bonus = (metrik.annual_rental_yield_pct - 5.0) * 0.02
    return {"durum": OK,
            "carpan": round(max(0.85, min(1.35, 1.0 + wealth_bonus + yield_bonus)), 4)}


if __name__ == "__main__":
    sonuc = fetch_region_valuation("Aydın", "Kuşadası", "İnönü Blv.")
    print("Endeksa durumu:", sonuc["durum"], "|", sonuc["sebep"])
    print("Çarpan:", compute_sosyal_imece_asset_multiplier(sonuc))
    print("Anahtar görünür mü:", "HAYIR (yalnızca var/yok sorulur)")
