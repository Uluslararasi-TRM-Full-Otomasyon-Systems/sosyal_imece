#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TRM Ticari Dünya - DNP Ajan (Agent-200)
Versiyon: 3.0.0
"""

import json
import time
import threading
import requests
from datetime import datetime
import logging

class DNP_Agent:
    def __init__(self):
        self.id = 200
        self.name = "Agent-200"
        self.role = "🔮 DNP Ajan | Sistem Bütünlük Denetimi"
        self.status = "active"
        self.orchestrator_url = "http://localhost:8080"
        self.last_heartbeat = None
        self.heartbeat_interval = 30  # saniye
        self.setup_logging()
        self.is_running = False
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] [Agent-200] %(levelname)s: %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger('DNP_Agent')
        self.logger.info("🔮 DNP Ajan başlatılıyor...")
    
    def register(self):
        """Orchestrator'a kaydol"""
        try:
            data = {
                "agent_id": self.id,
                "name": self.name,
                "status": self.status
            }
            response = requests.post(
                f"{self.orchestrator_url}/api/agents/register",
                json=data,
                timeout=10
            )
            if response.status_code == 200:
                self.logger.info("✅ Orchestrator'a başarıyla kaydedildi")
                return True
            else:
                self.logger.error(f"❌ Kayıt hatası: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Bağlantı hatası: {e}")
            return False
    
    def send_heartbeat(self):
        """Orchestrator'a heartbeat gönder"""
        try:
            data = {
                "agent_id": self.id,
                "status": self.status,
                "timestamp": datetime.now().isoformat()
            }
            response = requests.post(
                f"{self.orchestrator_url}/api/agents/heartbeat",
                json=data,
                timeout=5
            )
            if response.status_code == 200:
                self.last_heartbeat = datetime.now()
                self.logger.debug("💓 Heartbeat gönderildi")
            else:
                self.logger.warning("⚠️ Heartbeat yanıtı başarısız")
        except Exception as e:
            self.logger.error(f"❌ Heartbeat hatası: {e}")
    
    def run_heartbeat(self):
        """Heartbeat döngüsünü çalıştır"""
        self.is_running = True
        while self.is_running:
            self.send_heartbeat()
            time.sleep(self.heartbeat_interval)
    
    def run(self):
        """Ajanı çalıştır"""
        self.logger.info("🔮 DNP Ajan çalışıyor...")
        
        # Orchestrator'a kaydol
        if not self.register():
            self.logger.error("❌ Kayıt başarısız, yeniden deneniyor...")
            time.sleep(5)
            self.register()
        
        # Heartbeat başlat
        self.run_heartbeat()


# ============================================
# ANA ÇALIŞTIRMA
# ============================================

if __name__ == "__main__":
    agent = DNP_Agent()
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n🛑 DNP Ajan durduruluyor...")
        agent.is_running = False