#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TRM Ticari Dünya - İçerik Oluşturucu Ajanı
Versiyon: 3.0.0

BaseAgent: trm_agents/base_agent_template.py
Bu ajan, AI ile içerik üretir ve sosyal medyaya gönderir.
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
# CONTENT CREATOR AGENT
# ============================================

class ContentCreatorAgent(BaseAgent):
    """
    AI ile içerik üreten ve sosyal medyaya gönderen ajan.
    BaseAgent'dan türetilmiştir.
    """
    
    def __init__(self, agent_name: str = "ContentCreator", agent_id: Optional[int] = None):
        """
        Ajan başlatma
        """
        super().__init__(agent_name, agent_id)
        
        # Config'ten değerleri oku
        self.content_type = self.get_config("content.type", "video")
        self.default_topic = self.get_config("content.default_topic", "teknoloji")
        self.platforms = self.get_config("social_media.platforms", ["YouTube", "TikTok"])
        
        self.content_count = 0
        self.last_content = None
        
        self.log(f"📝 İçerik tipi: {self.content_type}", "INFO")
        self.log(f"🎯 Varsayılan konu: {self.default_topic}", "INFO")
        
        self.status = "ready"
    
    # ============================================
    # ANA METODLAR
    # ============================================
    
    def run(self, topic: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        ★★★ BaseAgent.run() implementasyonu ★★★
        İçerik üretir ve gönderir.
        """
        try:
            self.log("🔄 İçerik üretimi başlatılıyor...", "INFO")
            
            # Parametre kontrolü
            if topic is None:
                topic = self.default_topic
                self.log(f"🎯 Varsayılan konu: {topic}", "INFO")
            
            # İçerik üret
            content = self.generate_content(topic)
            
            # İçeriği platformlara gönder
            results = self.distribute_content(content)
            
            # İstatistikleri güncelle
            self.content_count += 1
            self.last_content = {
                "topic": topic,
                "timestamp": datetime.now().isoformat(),
                "content": content[:100] + "..." if len(content) > 100 else content
            }
            
            self.log(f"✅ İçerik üretildi ve {len(results)} platforma gönderildi", "INFO")
            
            return {
                "status": "success",
                "content": content,
                "topic": topic,
                "distribution": results,
                "content_count": self.content_count
            }
            
        except Exception as e:
            self.log(f"❌ İçerik üretim hatası: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return {"status": "error", "error": str(e)}
    
    def generate_content(self, topic: str) -> str:
        """
        AI ile içerik üretir (simülasyon)
        """
        self.log(f"🤖 İçerik üretiliyor: {topic}", "INFO")
        
        # ★★★ Gerçek AI entegrasyonu buraya ★★★
        # Simülasyon
        content = f"Bu {topic} konulu harika bir içerik! #TRMTicari #AI"
        
        time.sleep(2)  # Simülasyon bekleme
        return content
    
    def distribute_content(self, content: str) -> List[Dict[str, Any]]:
        """
        İçeriği platformlara dağıtır
        """
        results = []
        for platform in self.platforms:
            self.log(f"📤 İçerik {platform}'a gönderiliyor...", "INFO")
            results.append({
                "platform": platform,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            })
            time.sleep(0.5)
        return results
    
    # ============================================
    # ZORUNLU METODLAR
    # ============================================
    
    def stop(self) -> None:
        self.log("🛑 Durduruluyor...", "INFO")
        self.status = "stopping"
        self.is_running = False
        self.stop_heartbeat()
        self.status = "stopped"
        self.log("✅ Durduruldu", "INFO")
    
    def restart(self) -> None:
        self.log("🔄 Yeniden başlatılıyor...", "INFO")
        self.stop()
        time.sleep(2)
        self.status = "restarting"
        self.start_heartbeat()
        self.status = "ready"
        self.log("✅ Yeniden başlatıldı", "INFO")
    
    # ============================================
    # DURUM
    # ============================================
    
    def get_status(self) -> Dict[str, Any]:
        base_status = super().get_status()
        base_status.update({
            "content_type": self.content_type,
            "content_count": self.content_count,
            "last_content": self.last_content,
            "platforms": self.platforms
        })
        return base_status


# ============================================
# TETİKLEYİCİ
# ============================================

def trigger_content_creator(topic: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Orkestratör tarafından çağrılan tetikleyici.
    """
    try:
        agent = ContentCreatorAgent()
        return agent.run(topic=topic, **kwargs)
    except Exception as e:
        import logging
        logging.error(f"❌ Tetikleyici hatası: {e}")
        return {"status": "error", "error": str(e)}


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    agent = ContentCreatorAgent(agent_id=10)
    result = agent.run(topic="yapay zeka")
    print(f"\n📊 Sonuç:\n{result}")
    
    print(f"\n📊 Durum:\n{agent.get_status()}")
    agent.stop()