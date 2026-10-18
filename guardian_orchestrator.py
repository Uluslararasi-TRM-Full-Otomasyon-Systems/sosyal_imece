#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TRM Ticari Dünya - Orchestrator
Versiyon: 3.0.0 (200 AJAN)
"""

import os
import json
import yaml
import logging
import time
import threading
import random
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from ultra_nirvana_guardian import UltraNirvanaGuardian
from database_manager import DatabaseManager

# ============================================
# YAPILANDIRMA
# ============================================

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config" / "global_config.json"
STATE_FILE = BASE_DIR / "state.yaml"
AGENTS_FILE = BASE_DIR / "data" / "agents.json"

class Orchestrator:
    def __init__(self):
        self.db = DatabaseManager()
        self.config = self.load_config()
        self.state = self.load_state()
        self.agents = self.load_agents()
        self.max_agents = self.config.get("sistem", {}).get("max_ajan_sayisi", 165)
        self.is_running = False
        self.guardian = UltraNirvanaGuardian()
        self.setup_logging()
        self.setup_server()
        
    def load_config(self):
        """config/global_config.json dosyasını yükle (standart, tek config kaynağı)"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ {CONFIG_FILE} bulunamadı, varsayılan oluşturuluyor...")
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            default_config = {
                "sistem": {
                    "max_ajan_sayisi": 165,
                    "log_klasoru": "./logs",
                    "rapor_klasoru": "./reports"
                },
                "sunucu": {"host": "0.0.0.0", "port": 8080}
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            return default_config
    
    def load_state(self):
        """state.yaml dosyasını yükle"""
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print("⚠️ state.yaml bulunamadı, varsayılan oluşturuluyor...")
            default_state = {
                "system": {"status": "idle"},
                "agents": {"total": 165, "active": 0}
            }
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(default_state, f)
            return default_state
    
    def load_agents(self):
        """agents.json dosyasını yükle (SQLite'dan)"""
        try:
            # SQLite'dan ajanları yükle
            return self.db.get_agents_dict()
        except Exception as e:
            print(f"⚠️ SQLite'dan ajan yüklenemedi: {e}")
            return {"total_agents": 0, "agents": []}
    
    def save_agents(self):
        """agents.json dosyasını kaydet (SQLite'a)"""
        # SQLite'a kaydetme - agents dict'i zaten güncel
        # Bu fonksiyon uyumluluk için tutuldu, aslında veriler doğrudan SQLite'a yazılıyor
        pass
    
    def setup_logging(self):
        """Logging ayarlarını yap"""
        log_dir = BASE_DIR / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'system.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Orchestrator')
        self.logger.info("🚀 Orchestrator başlatılıyor...")
        self.logger.info(f"📊 Maksimum Ajan: {self.max_agents}")
    
    def setup_server(self):
        """Flask sunucusunu kur"""
        self.app = Flask(__name__)
        CORS(self.app)
        self.setup_routes()
        self.host = self.config.get("sunucu", {}).get("host", "0.0.0.0")
        self.port = self.config.get("sunucu", {}).get("port", 8080)
    
    def setup_routes(self):
        """API rotalarını tanımla"""
        
        @self.app.route('/')
        def index():
            return jsonify({
                "system": "TRM Ticari Dünya Orchestrator",
                "version": "3.0.0",
                "status": "running",
                "max_agents": self.max_agents,
                "active_agents": len([a for a in self.agents.get("agents", []) if a.get("status") == "active"])
            })
        
        @self.app.route('/api/agents')
        def get_agents():
            return jsonify(self.db.get_agents_dict())
        
        @self.app.route('/api/agents/count')
        def get_agent_count():
            active = self.db.get_active_agents_count()
            total = self.db.get_total_agents_count()
            return jsonify({
                "total": total,
                "active": active,
                "inactive": total - active
            })
        
        @self.app.route('/api/agents/sync', methods=['POST'])
        def sync_agents():
            data = request.json
            target_count = data.get("max_ajan_sayisi", self.max_agents)
            
            # Ajan sayısını güncelle
            self.max_agents = target_count
            self.config.setdefault("sistem", {})["max_ajan_sayisi"] = target_count
            
            # Ajanları oluştur
            self.create_agents(target_count)
            
            self.save_agents()
            self.save_config()
            
            self.logger.info(f"✅ {target_count} ajan senkronize edildi")
            return jsonify({
                "success": True,
                "max_agents": target_count,
                "message": f"{target_count} ajan senkronize edildi"
            })
        
        @self.app.route('/api/agents/register', methods=['POST'])
        def register_agent():
            data = request.json
            agent_id = data.get("agent_id")
            agent_name = data.get("name", f"Agent-{agent_id:03d}")
            
            # Ultra Nirvana Guardian: İnsan davranışı simülasyonu
            human_delay = self.guardian.human_behavior_simulation(agent_name)
            self.logger.info(f"🧠 İnsan davranışı simülasyonu: {human_delay:.2f}s")
            
            # Ultra Nirvana Guardian: Risk analizi
            risk_score = data.get("risk_score", 0.1)  # Varsayılan düşük risk
            quarantine_check = self.guardian.dynamic_agent_quarantine_check(agent_id, risk_score)
            
            if not quarantine_check:
                return jsonify({"success": False, "message": "Ajan karantinaya alındı - yüksek risk"}), 403
            
            # Ajanı SQLite'a ekle veya güncelle
            existing = self.db.get_agent_by_id(agent_id)
            
            if existing:
                # Güncelle
                agent_data = {
                    "id": agent_id,
                    "name": agent_name,
                    "role": data.get("role", existing.get("role")),
                    "web": data.get("web", existing.get("web")),
                    "status": data.get("status", existing.get("status")),
                    "last_heartbeat": datetime.now().isoformat()
                }
                self.db.insert_agent(agent_data)
                self.logger.info(f"🔄 Ajan {agent_id} güncellendi")
            else:
                # Yeni ajan
                new_agent = {
                    "id": agent_id,
                    "name": agent_name,
                    "role": data.get("role", "Standard Agent"),
                    "web": data.get("web", "trendurunlermarket.com"),
                    "status": data.get("status", "active"),
                    "last_heartbeat": datetime.now().isoformat()
                }
                self.db.insert_agent(new_agent)
                self.logger.info(f"✅ Yeni ajan kaydedildi: {agent_name}")
            
            # Guardian: Operasyon kaydı
            self.guardian.record_operation(agent_id, "register")
            
            # Güncel ajan verisini döndür
            updated_agent = self.db.get_agent_by_id(agent_id)
            return jsonify({"success": True, "agent": updated_agent})
        
        @self.app.route('/api/status')
        def get_status():
            active = self.db.get_active_agents_count()
            return jsonify({
                "status": "running",
                "max_agents": self.max_agents,
                "active_agents": active,
                "uptime": self.get_uptime(),
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.route('/api/heal', methods=['POST'])
        def trigger_healing():
            data = request.json
            self.logger.info(f"🔧 Self-Healing tetiklendi: {data}")
            return jsonify({"success": True, "message": "Self-Healing başlatıldı"})
    
    def create_agents(self, count):
        """Belirtilen sayıda ajan oluştur"""
        roles = [
            "Yapay Zeka Araştırması", "Pazar Analizi", "Rakip Takibi", "Veri Madenciliği",
            "İçerik Üretimi", "Sosyal Medya Yönetimi", "SEO Optimizasyonu", "Müşteri Desteği",
            "Otomasyon Geliştirme", "Güvenlik Taraması", "Finans Analizi", "Trend Belirleme",
            "Dil İşleme", "Görüntü Tanıma", "Ses Analizi", "Robotik Kontrol"
        ]
        webs = ["trendurunlermarket.com", "dunya.ai", "yardim.com", "kooperatif.org", "dayanisma.net"]
        
        agents = []
        for i in range(1, count + 1):
            role_idx = (i - 1) % len(roles)
            web_idx = (i - 1) % len(webs)
            
            # Ultra Nirvana Guardian: İnsan davranışı simülasyonu
            agent_name = f"Agent-{i:03d}"
            human_delay = self.guardian.human_behavior_simulation(agent_name)
            
            # Ultra Nirvana Guardian: Risk analizi (rastgele düşük risk)
            risk_score = random.uniform(0.0, 0.3)
            quarantine_check = self.guardian.dynamic_agent_quarantine_check(i, risk_score)
            
            if not quarantine_check:
                self.logger.warning(f"⚠️ Ajan {i} karantinaya alındı - atlanıyor")
                continue
            
            if i == 1:
                role = "🐉 Başkomutan | Tüm sistemi yönetir"
                web = "mehmet.ai"
            elif i <= 10:
                role = f"📊 Komuta - {roles[role_idx]}"
                web = webs[web_idx]
            elif i == count and count >= 161:
                role = "🔮 DNP Ajan | Sistem Bütünlük Denetimi"
                web = "dnp.trendurunlermarket.com"
            else:
                role = f"📁 Veri - {roles[role_idx]}"
                web = webs[web_idx]
            
            agents.append({
                "id": i,
                "name": agent_name,
                "role": role,
                "web": web,
                "status": "active" if i <= 10 else "inactive",
                "last_heartbeat": datetime.now().isoformat()
            })
            
            # Guardian: Operasyon kaydı
            self.guardian.record_operation(i, "create")
        
        # Ajanları SQLite'a kaydet
        for agent in agents:
            self.db.insert_agent(agent)
        
        self.agents = {
            "total_agents": len(agents),
            "agents": agents
        }
        self.logger.info(f"✅ {len(agents)} ajan oluşturuldu ve SQLite'a kaydedildi")
    
    def save_config(self):
        """config/global_config.json dosyasını kaydet"""
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def get_uptime(self):
        """Sistem çalışma süresini döndür"""
        return "0s"  # Gerçek uptime için değiştirilebilir
    
    def run(self):
        """Orchestrator'ı çalıştır"""
        self.is_running = True
        self.logger.info(f"🌐 Sunucu başlatılıyor: http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=True, use_reloader=False)


# ============================================
# ANA ÇALIŞTIRMA
# ============================================

if __name__ == "__main__":
    orchestrator = Orchestrator()
    
    # Varsayılan ajanları oluştur
    orchestrator.create_agents(orchestrator.max_agents)
    
    # Sunucuyu başlat
    orchestrator.run()