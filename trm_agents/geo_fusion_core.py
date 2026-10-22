# -*- coding: utf-8 -*-
"""Geo fusion raporu — FAIL-CLOSED.

Eski hâli hiçbir modüle sormadan `"status": "synced"`, `"accuracy": "%99.4"`,
`"vibe_check": "Optimized"`, `regional_fulfillment_readiness: High` ve
"Aktif bölge bazlı dinamik fiyatlandırma devrede" gibi olmayan özellikleri
rapora yazıyordu. Bu sürüm raporu modüllerin kendisinden okur: alt yapılandırma
yoksa rapor `not_configured` yazar ve neyin eksik olduğunu sebep olarak taşır.
"""

import os
import json
import logging
from datetime import datetime

import config

from .hoodmaps_integration import HoodmapsIntegration
from .geospy_integration import GeoSpyIntegration
from .endeksa_integration import EndeksaIntegration
from .withraven_integration import WithRavenIntegration

logger = logging.getLogger("GeoFusionCore")

NOT_CONFIGURED = "not_configured"


def _durum(servis, konu: str) -> dict:
    """Bir entegrasyon modülüne gerçekte ne bildirdiğini sor."""
    yontem = getattr(servis, konu, None)
    sonuc = yontem("Raporlama provası") if callable(yontem) else None
    if isinstance(sonuc, dict):
        return {"durum": sonuc.get("durum", NOT_CONFIGURED),
                "sebep": sonuc.get("sebep", "modül durum bildirmiyor"),
                "veri": None}
    return {"durum": getattr(servis, "durum", NOT_CONFIGURED),
            "sebep": "modül durum bildirmiyor", "veri": None}


class GeoEcommerceFusionEngine:
    def __init__(self):
        self.system_name = config._cfg.get("system_name", "TRM TICARI EKOSISTEMI")
        self.version = config._cfg.get("version", "3.0.0")
        self.max_agents = config._cfg.get("max_agents", 165)
        self.hoodmaps = HoodmapsIntegration()
        self.geospy = GeoSpyIntegration()
        self.endeksa = EndeksaIntegration()
        self.withraven = WithRavenIntegration()

    def run_fusion_analysis(self):
        """Modüllerin kendi bildirdiği durumları rapora yazar; veri üretmez."""
        moduller = {
            "hoodmaps_integration": _durum(self.hoodmaps, "get_cultural_insights"),
            "geospy_integration": _durum(self.geospy, "get_location_intelligence"),
            "endeksa_integration": _durum(self.endeksa, "analyze_luxury_product_fit"),
            "withraven_integration": _durum(self.withraven, "process_geographic_data"),
        }
        canli = [ad for ad, bilgi in moduller.items() if bilgi["durum"] == "ok"]
        fusion_durumu = "active" if len(canli) == len(moduller) else NOT_CONFIGURED

        rapor = {
            "fusion_status": fusion_durumu,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "system_config": {
                "system_name": self.system_name,
                "version": self.version,
                "max_agents": self.max_agents,
            },
            "modules": moduller,
            "canli_modul_sayisi": len(canli),
            "aciklama": (
                "Gerçek coğrafi aday taraması OSM/Overpass üzerinden yapılır ve "
                "ODbL atfıyla aday_havuzu.py'da raporlanır. Bu rapordaki "
                "ticari istihbarat modülleri lisanslı besleme olmadan veri "
                "üretmez."
            ),
            "ecaret": {
                "storefront": "www.trendurunlermarket.com",
                "dinamik_fiyatlandirma": NOT_CONFIGURED,
                "bolgesel_fulfillment": NOT_CONFIGURED,
            },
        }

        os.makedirs("reports", exist_ok=True)
        report_path = "reports/geo_fusion_master_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(rapor, f, ensure_ascii=False, indent=4)

        logger.info(f"Fusion raporu yazıldı: {report_path} -> {fusion_durumu}")
        return rapor


if __name__ == "__main__":
    print(json.dumps(GeoEcommerceFusionEngine().run_fusion_analysis(),
                     indent=2, ensure_ascii=False))
