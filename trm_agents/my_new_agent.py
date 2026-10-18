#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TRM Ticari Dünya - [AJAN_ADI] Ajanı
Versiyon: 3.0.0

BaseAgent: trm_agents/base_agent_template.py
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

# ★★★ BaseAgent import ★★★
try:
    from trm_agents.base_agent_template import BaseAgent
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from trm_agents.base_agent_template import BaseAgent

# ============================================
# AJAN SINIFI
# ============================================

class MyNewAgent(BaseAgent):
    """
    [AJAN AÇIKLAMASI]
    BaseAgent'dan türetilmiştir.
    """
    
    def __init__(self, agent_name: str = "MyNewAgent", agent_id: Optional[int] = None):
        """
        Ajan başlatma
        """
        # ★★★ BaseAgent init çağrısı ZORUNLU ★★★
        super().__init__(agent_name, agent_id)
        
        # ★★★ KENDİ BAŞLATMA KODLARINIZ ★★★
        self.my_variable = self.get_config("my_section.my_key", "default_value")
        
        self.log(f"🚀 {self.agent_name} başlatıldı", "INFO")
        self.status = "ready"
    
    # ============================================
    # ANA METODLAR (ZORUNLU)
    # ============================================
    
    def run(self, **kwargs) -> Any:
        """
        ★★★ BaseAgent.run() implementasyonu ★★★
        Ana çalıştırma metodu.
        """
        try:
            self.log("🔄 Çalıştırılıyor...", "INFO")
            
            # ★★★ KENDİ KODUNUZ ★★★
            # Örnek: 
            # video_path = kwargs.get('video_path', self.default_video)
            # result = self.process_video(video_path)
            
            return {"status": "success", "result": "İşlem tamamlandı"}
            
        except Exception as e:
            self.log(f"❌ Hata: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return {"status": "error", "error": str(e)}
    
    def stop(self) -> None:
        """
        ★★★ BaseAgent.stop() implementasyonu ★★★
        Ajanı durdurur.
        """
        self.log("🛑 Durduruluyor...", "INFO")
        self.status = "stopping"
        self.is_running = False
        self.stop_heartbeat()
        self.status = "stopped"
        self.log("✅ Durduruldu", "INFO")
    
    def restart(self) -> None:
        """
        ★★★ BaseAgent.restart() implementasyonu ★★★
        Ajanı yeniden başlatır.
        """
        self.log("🔄 Yeniden başlatılıyor...", "INFO")
        self.stop()
        time.sleep(2)
        self.status = "restarting"
        self.start_heartbeat()
        self.status = "ready"
        self.log("✅ Yeniden başlatıldı", "INFO")
    
    # ============================================
    # OPSİYONEL: ÖZEL METODLAR
    # ============================================
    
    def process_video(self, video_path: str) -> Dict[str, Any]:
        """
        Özel işlem metodu (örnek)
        """
        self.log(f"🎬 Video işleniyor: {video_path}", "INFO")
        # İşlem kodları...
        return {"processed": True, "path": video_path}
    
    # ============================================
    # OPSİYONEL: HEARTBEAT OLAYI
    # ============================================
    
    def on_heartbeat(self, heartbeat_data: Dict[str, Any]) -> None:
        """
        Heartbeat olayında yapılacak işlemler (opsiyonel)
        """
        # Örneğin her heartbeat'te bir işlem yapmak isterseniz
        pass
    
    # ============================================
    # OPSİYONEL: DURUM
    # ============================================
    
    def get_status(self) -> Dict[str, Any]:
        """
        Ajan durumunu döndürür (opsiyonel override)
        """
        base_status = super().get_status()
        base_status.update({
            "my_custom_value": self.my_variable,
            "custom_status": "OK"
        })
        return base_status


# ============================================
# TETİKLEYİCİ FONKSİYON (Orkestratör için)
# ============================================

def trigger_my_new_agent(**kwargs) -> Any:
    """
    Orkestratör tarafından çağrılan tetikleyici.
    """
    try:
        agent = MyNewAgent()
        return agent.run(**kwargs)
    except Exception as e:
        import logging
        logging.error(f"❌ Tetikleyici hatası: {e}")
        return {"status": "error", "error": str(e)}


# ============================================
# BAĞIMSIZ ÇALIŞTIRMA (Test için)
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("MY NEW AGENT - TEST")
    print("=" * 60)
    
    # Ajan oluştur
    agent = MyNewAgent(agent_id=100)
    
    # Çalıştır
    result = agent.run()
    print(f"Sonuç: {result}")
    
    # Durumu göster
    print(f"Durum: {agent.get_status()}")
    
    # Durdur
    agent.stop()