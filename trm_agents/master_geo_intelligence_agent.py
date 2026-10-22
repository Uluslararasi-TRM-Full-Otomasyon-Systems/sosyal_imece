#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Master Geo Intelligence Agent — FAIL-CLOSED.

Eski hâli dört alt modülün uydurduğu yaş/gelir/refah ve skor değerlerini
toplayıp `overall_intelligence_score` üretiyor, ayrıca `analyze_demographic_targeting`
("age_range": "25-45", "income": "middle") ve `analyze_luxury_targeting` ile
tüketici hedeflemesi yapıyordu. Bu sürüm:

- hiçbir sayı üretmez; alt modüller `not_configured` bildiriyorsa sonuç da
  `not_configured` döner ve skor `None` kalır,
- tüketici/demografik hedefleme metodları tamamen kaldırıldı,
- meşru coğrafi hat tek gerçektir: OSM/Overpass ticari POI taraması
  (`aday_havuzu.py`) ve operatör panelinden onaylanmış esnaf kayıtları.
"""

import os
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_agent_template import BaseAgent
from .hoodmaps_integration import HoodmapsIntegration
from .geospy_integration import GeoSpyIntegration
from .endeksa_integration import EndeksaIntegration
from .withraven_integration import WithRavenIntegration

logger = logging.getLogger(__name__)

NOT_CONFIGURED = "not_configured"
OK = "ok"


class MasterGeoIntelligenceAgent(BaseAgent):
    """Coğrafi istihbarat araçlarını çalıştırır, ama veri uydurmaz."""

    def __init__(self, agent_id: Optional[int] = None):
        super().__init__(
            agent_name="Master Geo Intelligence Agent",
            agent_id=agent_id if agent_id else 168,
        )
        self.hoodmaps = HoodmapsIntegration()
        self.geospy = GeoSpyIntegration()
        self.endeksa = EndeksaIntegration()
        self.withraven = WithRavenIntegration()
        self.geo_intelligence_cache = {}
        self.analysis_history = []
        self.log("🌍 Master Coğrafi İstihbarat Ajanı başlatıldı (fail-closed)", "INFO")

    # ============================================
    # ANA METODLAR (BaseAgent override)
    # ============================================

    def run(self, **kwargs) -> Dict[str, Any]:
        target_location = str(kwargs.get("target_location") or "").strip()
        analysis_type = kwargs.get("analysis_type", "comprehensive")
        self.status = "running"

        try:
            moduller = self._modul_durumlari(target_location)
            canli = [ad for ad, b in moduller.items() if b.get("durum") == OK]
            sonuc = {
                "analysis_timestamp": datetime.now().isoformat(),
                "target_location": target_location or "(belirtilmedi)",
                "analysis_type": analysis_type,
                "durum": OK if len(canli) == len(moduller) else NOT_CONFIGURED,
                "modules": moduller,
                # Skor yalnızca gerçek besleyici veriden gelir; burada asla
                # sabit ya da türetilmiş tahmin yazılmaz.
                "overall_intelligence_score": None,
                "canli_modul_sayisi": len(canli),
                "modul_toplam": len(moduller),
                "asil_cografi_kaynak": (
                    "aday_havuzu.py / OSM Overpass (ODbL atfıyla) — "
                    "ticari POI + ilce/mahalle etiketleri"
                ),
            }
            self._save_analysis_result(sonuc)
            self.status = "completed"
            self.log(
                f"Coğrafi istihbarat provası: {sonuc['durum']} "
                f"({len(canli)}/{len(moduller)} modül canlı)", "INFO")
            return sonuc
        except Exception as exc:
            self.status = "error"
            self.log(f"❌ Coğrafi istihbarat analizi hatası: {exc}", "ERROR")
            raise

    def stop(self) -> None:
        self.status = "stopped"
        self.log("⏹️ Master Coğrafi İstihbarat Ajanı durduruldu", "INFO")

    def restart(self) -> None:
        self.log("🔄 Master Coğrafi İstihbarat Ajanı yeniden başlatılıyor...", "INFO")
        self.status = "restarting"
        self.geo_intelligence_cache = {}
        self.analysis_history = []
        self.status = "ready"
        self.log("✅ Yeniden başlatma tamamlandı", "INFO")

    # ============================================
    # YARDIMCI METODLAR
    # ============================================

    def _modul_durumlari(self, lokasyon: str) -> Dict[str, Dict[str, Any]]:
        """Her alt modüle durumunu sor; cevabı hiç değiştirmeden rapora koy."""
        prova = lokasyon or "-"
        return {
            "hoodmaps_integration": self._sor(
                self.hoodmaps.get_cultural_insights, prova),
            "geospy_integration": self._sor(
                self.geospy.get_location_intelligence, prova),
            "endeksa_integration": self._sor(
                self.endeksa.get_elite_audience_profile, prova),
            "withraven_integration": self._sor(
                self.withraven.process_geographic_data, {}),
        }

    @staticmethod
    def _sor(fonksiyon, girdi: Any) -> Dict[str, Any]:
        sonuc = fonksiyon(girdi)
        if isinstance(sonuc, dict):
            return {"durum": sonuc.get("durum", NOT_CONFIGURED),
                    "sebep": sonuc.get("sebep", "modül sebep bildirmedi")}
        return {"durum": NOT_CONFIGURED, "sebep": "modül sözlük döndürmedi"}

    def _save_analysis_result(self, result: Dict[str, Any]) -> bool:
        try:
            self.analysis_history.append(result)
            state_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "geo_intelligence_analysis.json")
            os.makedirs(os.path.dirname(state_file), exist_ok=True)
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            return True
        except Exception as exc:
            self.log(f"❌ Analiz sonucu kaydetme hatası: {exc}", "ERROR")
            return False

    def get_analysis_history(self) -> List[Dict[str, Any]]:
        return self.analysis_history


if __name__ == "__main__":
    agent = MasterGeoIntelligenceAgent(agent_id=168)
    print(json.dumps(agent.run(target_location="Aydın"), indent=2,
                     ensure_ascii=False))
