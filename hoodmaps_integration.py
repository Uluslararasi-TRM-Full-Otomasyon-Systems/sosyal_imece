# -*- coding: utf-8 -*-
"""Hoodmaps entegrasyonu — FAIL-CLOSED (tüketici hedeflemesi olarak da KAPALI).

Eski hâli iki elle yazılmış sahte kayıt ("ayıdin_kusadasi_inonu: emekli
eğilimi 89.5, ticari yoğunluk 82.0" gibi) ve eşleşmeyen HER bölge için
75.0/70.0 uydurma skor döndürüyordu. Üstelik `targets_55_plus_wealth_pool` ile
mahalledeki tüketicileri yaş/refah göre hedefliyordu — bu, ticari onay akışına
hiçbir şekilde girmemesi gereken bir tüketici hedeflemesidir.

Şimdi:
  * tek bir veri bile üretilmez; durum daima `not_configured`;
  * tüketici demografisi (yaş/refah/eğilim) skorlayan hiçbir alan kalmaz;
  * Hoodmaps'in kendisi API sunmaz, kazımak hizmet şartlarına aykırıdır; bu
    yüzden "anahtar gelirse açılır" bir yol da yoktur. Ticari POI/addr
    verisinin meşru kaynağı OpenStreetMap'tir (aday_havuzu.py, ODbL atfıyla).
"""

import logging
from typing import Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("HoodmapsIntegration")

NOT_CONFIGURED = "not_configured"
SEBEP = ("Hoodmaps API'si yok; kazımak hizmet şartlarına aykırı. "
         "Coğrafi filtre yalnızca OSM ticari POI verisi ve onaylı esnaf "
         "kayıtlarıyla yapılır (aday_havuzu).")


def mahalle_profili(city: str, district: str, neighborhood: str) -> Dict[str, object]:
    """Dürüst red: profil uydurulmaz, tüketici hedeflemesi üretilmez."""
    logger.warning(f"Hoodmaps -> not_configured ({city}/{district}/{neighborhood})")
    return {"durum": NOT_CONFIGURED, "sebep": SEBEP, "city": city, "district": district,
            "neighborhood": neighborhood}


class HoodmapsIntegration:
    """Geriye dönük isim: çağrılayanlar durum okuyamasın diye red döner."""

    durum = NOT_CONFIGURED
    sebep = SEBEP

    def analyze_neighborhood_identity(self, city: str, district: str,
                                      neighborhood: str) -> Dict[str, object]:
        return mahalle_profili(city, district, neighborhood)

    def get_neighborhood_demographics(self, location: str) -> Dict[str, object]:
        return mahalle_profili(location, "", "")

    def get_cultural_insights(self, location: str) -> Dict[str, object]:
        return mahalle_profili(location, "", "")


if __name__ == "__main__":
    print(mahalle_profili("Aydın", "Kuşadası", "İnönü"))
