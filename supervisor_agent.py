# supervisor_agent.py
import logging
from typing import Dict, Any, Callable

logging.basicConfig(level=logging.INFO, format="[QualitySupervisor] %(asctime)s - %(levelname)s - %(message)s")

class QualitySupervisorAgent:
    def __init__(self, retry_callback: Callable[[str, Dict[str, Any]], None] = None):
        self.retry_callback = retry_callback
        logging.info("QualitySupervisorAgent başlatıldı ve denetime hazır.")

    def evaluate_output(self, agent_name: str, payload: Dict[str, Any]) -> bool:
        """
        Ajan çıktısını denetler:
        - Boş payload kontrolü
        - Zorunlu alanlar / link bütünlüğü (trendurunlermarket.com)
        """
        if not payload or not isinstance(payload, dict):
            logging.warning(f"❌ [{agent_name}] geçersiz veya boş çıktı üretti.")
            self._trigger_retry(agent_name, payload)
            return False

        # Örnek kural: İçerik üretici veya pazarlama ajanıysa link içermeli veya metin boş olmamalı
        content_text = payload.get("content", "")
        target_url = payload.get("url", "trendurunlermarket.com")

        if agent_name == "ContentCreator" and not content_text:
            logging.warning(f"❌ [{agent_name}] metin içeriği eksik!")
            self._trigger_retry(agent_name, payload)
            return False

        if "trendurunlermarket.com" not in str(payload) and agent_name in ["ContentCreator", "AffiliateDispatcher"]:
            logging.warning(f"⚠️ [{agent_name}] çıktısında hedef domain referansı eksik görünüyor, uyarı verildi.")

        logging.info(f"✅ [{agent_name}] denetimi başarıyla onaylandı.")
        return True

    def _trigger_retry(self, agent_name: str, payload: Dict[str, Any]):
        logging.info(f"🔄 [{agent_name}] için yeniden deneme (retry) sinyali tetikleniyor...")
        if self.retry_callback:
            self.retry_callback(agent_name, payload)