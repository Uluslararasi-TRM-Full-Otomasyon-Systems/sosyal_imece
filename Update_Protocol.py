#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TRM NIRVANA v3.0 - Update Protocol
200 Ajanlı Merkezi Güncelleme Sistemi
Modüler, asenkron, jitter destekli

@author: Mehmet - TRM NIRVANA Ekibi
@version: 1.0.0
"""

import asyncio
import json
import os
import random
import logging
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# ============================================================
# KONFİGÜRASYON
# ============================================================

CONFIG = {
    "master_repo": "TRM",
    "agents_dir": "agents",
    "config_file": "config.json",
    "log_file": "update_protocol.log",
    "jitter_min": 0.1,
    "jitter_max": 0.5,
    "safety_threshold": 2.0,  # %2 hata oranı
    "timeout": 30,
    "max_retries": 3
}

# ============================================================
# LOGGING YAPILANDIRMASI
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["log_file"], encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("UpdateProtocol")

# ============================================================
# MERKEZİ KONFİGÜRASYON YÜKLEYİCİ
# ============================================================

class MasterConfig:
    """Merkezi konfigürasyon deposu (TRM)"""
    
    def __init__(self, repo_path: str = CONFIG["master_repo"]):
        self.repo_path = Path(repo_path)
        self.config_path = self.repo_path / CONFIG["config_file"]
        self._config: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Merkezi konfigürasyonu yükle"""
        if not self.config_path.exists():
            logger.warning(f"⚠️ Merkezi config dosyası bulunamadı: {self.config_path}")
            self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.info(f"✅ Merkezi config yüklendi: {len(self._config)} parametre")
        except Exception as e:
            logger.error(f"❌ Config yükleme hatası: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Varsayılan konfigürasyon oluştur"""
        self._config = {
            "api_key": "TRM_NIRVANA_API_KEY",
            "threshold": 0.85,
            "task_priority": ["sales", "content", "seo", "finance"],
            "version": "3.1.0",
            "last_update": datetime.now().isoformat(),
            "safety_threshold": CONFIG["safety_threshold"],
            "global_parameters": {
                "max_retries": CONFIG["max_retries"],
                "timeout": CONFIG["timeout"],
                "jitter_enabled": True
            }
        }
        self.repo_path.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=4, ensure_ascii=False)
        logger.info(f"✅ Varsayılan config oluşturuldu: {self.config_path}")
    
    @property
    def config(self) -> Dict[str, Any]:
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Konfigürasyonu güncelle ve kaydet"""
        self._config.update(updates)
        self._config["last_update"] = datetime.now().isoformat()
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=4, ensure_ascii=False)
        logger.info(f"✅ Merkezi config güncellendi: {len(updates)} parametre")

# ============================================================
# AJAN KONFİGÜRASYON YÖNETİCİSİ
# ============================================================

class AgentConfig:
    """Her ajanın yerel config.json dosyasını yönetir"""
    
    def __init__(self, agent_id: int, agents_dir: str = CONFIG["agents_dir"]):
        self.agent_id = agent_id
        self.agent_code = f"Agent-{agent_id:03d}"
        self.agents_dir = Path(agents_dir)
        self.config_path = self.agents_dir / f"ajan_{agent_id:03d}" / CONFIG["config_file"]
        self._config: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Ajanın yerel config'ini yükle"""
        if not self.config_path.exists():
            logger.debug(f"ℹ️ {self.agent_code} config dosyası yok, varsayılan oluşturuluyor.")
            self._create_default()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.debug(f"✅ {self.agent_code} config yüklendi")
        except Exception as e:
            logger.error(f"❌ {self.agent_code} config yükleme hatası: {e}")
            self._create_default()
    
    def _create_default(self) -> None:
        """Varsayılan ajan config'i oluştur"""
        self._config = {
            "agent_id": self.agent_id,
            "agent_code": self.agent_code,
            "api_key": "",
            "threshold": 0.85,
            "task_priority": ["sales", "content", "seo"],
            "version": "1.0.0",
            "last_update": datetime.now().isoformat(),
            "metrics": {
                "success_count": 0,
                "error_count": 0,
                "total_operations": 0,
                "success_rate": 100.0,
                "error_rate": 0.0
            },
            "status": "idle"
        }
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=4, ensure_ascii=False)
        logger.debug(f"✅ {self.agent_code} varsayılan config oluşturuldu")
    
    @property
    def config(self) -> Dict[str, Any]:
        return self._config
    
    def update(self, master_config: Dict[str, Any]) -> bool:
        """
        Merkezi config'den alınan parametrelerle ajan config'ini güncelle
        Returns: True if updated successfully, False if safety mode triggered
        """
        # Hata oranını kontrol et
        error_rate = self._config.get("metrics", {}).get("error_rate", 0)
        
        if error_rate > CONFIG["safety_threshold"]:
            logger.warning(f"⚠️ {self.agent_code} SAFETY MODE - Hata oranı: %{error_rate:.2f}")
            self._config["status"] = "safety_mode"
            self._save()
            return False
        
        # Güncelleme yap
        self._config["api_key"] = master_config.get("api_key", self._config.get("api_key", ""))
        self._config["threshold"] = master_config.get("threshold", self._config.get("threshold", 0.85))
        self._config["task_priority"] = master_config.get("task_priority", self._config.get("task_priority", []))
        self._config["version"] = master_config.get("version", self._config.get("version", "1.0.0"))
        self._config["last_update"] = datetime.now().isoformat()
        self._config["status"] = "updated"
        
        self._save()
        logger.info(f"✅ {self.agent_code} güncellendi - Version: {self._config['version']}")
        return True
    
    def _save(self) -> None:
        """Config'i kaydet"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ {self.agent_code} config kaydetme hatası: {e}")
    
    def record_operation(self, success: bool) -> None:
        """İşlem sonucunu kaydet ve metrikleri güncelle"""
        metrics = self._config.setdefault("metrics", {})
        metrics["total_operations"] = metrics.get("total_operations", 0) + 1
        
        if success:
            metrics["success_count"] = metrics.get("success_count", 0) + 1
        else:
            metrics["error_count"] = metrics.get("error_count", 0) + 1
        
        # Oranları hesapla
        total = metrics["total_operations"]
        if total > 0:
            metrics["success_rate"] = (metrics["success_count"] / total) * 100
            metrics["error_rate"] = (metrics["error_count"] / total) * 100
        
        self._save()

# ============================================================
# UPDATE PROTOCOL - ANA ORKESTRATÖR
# ============================================================

class UpdateProtocol:
    """Tüm ajanları güncelleyen ana protokol"""
    
    def __init__(self):
        self.master = MasterConfig()
        self.agents: Dict[int, AgentConfig] = {}
        self.results: Dict[int, Dict[str, Any]] = {}
        self.safety_mode_agents: list = []
        self.updated_agents: list = []
        self._lock = asyncio.Lock()
    
    async def initialize_agents(self, count: int = 200) -> None:
        """Tüm ajan konfigürasyonlarını başlat"""
        logger.info(f"🚀 {count} ajan başlatılıyor...")
        for i in range(1, count + 1):
            agent = AgentConfig(i)
            self.agents[i] = agent
        logger.info(f"✅ {len(self.agents)} ajan başlatıldı")
    
    async def update_agent(self, agent_id: int) -> Dict[str, Any]:
        """
        Tek bir ajana güncelleme gönderir (Jitter ile)
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return {"agent_id": agent_id, "status": "not_found"}
        
        # Jitter - rastgele gecikme
        jitter = random.uniform(CONFIG["jitter_min"], CONFIG["jitter_max"])
        await asyncio.sleep(jitter)
        
        result = {
            "agent_id": agent_id,
            "agent_code": agent.agent_code,
            "jitter": jitter,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Güncellemeyi dene
            updated = agent.update(self.master.config)
            
            if updated:
                result["status"] = "ID_Updated_Success"
                async with self._lock:
                    self.updated_agents.append(agent_id)
                logger.info(f"✅ {agent.agent_code} güncellendi (jitter: {jitter:.3f}s)")
            else:
                # Safety mode
                result["status"] = "Safety_Mode_Active"
                result["error_rate"] = agent.config.get("metrics", {}).get("error_rate", 0)
                async with self._lock:
                    self.safety_mode_agents.append(agent_id)
                logger.warning(f"⚠️ {agent.agent_code} SAFETY MODE aktif!")
                
                # Mehmet'e bildir
                await self.notify_mehmet(agent_id, result)
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"❌ {agent.agent_code} güncelleme hatası: {e}")
        
        return result
    
    async def update_all_agents(self) -> Dict[str, Any]:
        """Tüm ajanları eş zamanlı olarak güncelle"""
        logger.info("🔄 Tüm ajanlar güncelleniyor...")
        
        # Tüm ajanları eş zamanlı çalıştır
        tasks = [self.update_agent(i) for i in range(1, len(self.agents) + 1)]
        results = await asyncio.gather(*tasks)
        
        # Sonuçları topla
        self.results = {r["agent_id"]: r for r in results}
        
        summary = {
            "total_agents": len(self.agents),
            "updated": len(self.updated_agents),
            "safety_mode": len(self.safety_mode_agents),
            "failed": len([r for r in results if r.get("status") == "error"]),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"""
        📊 GÜNCELLEME ÖZETİ:
        - Toplam Ajan: {summary['total_agents']}
        - Başarılı Güncelleme: {summary['updated']}
        - Safety Mode: {summary['safety_mode']}
        - Başarısız: {summary['failed']}
        """)
        
        return summary
    
    async def notify_mehmet(self, agent_id: int, result: Dict[str, Any]) -> None:
        """
        Safety mode durumunda Mehmet'e bildirim gönderir
        """
        message = f"""
        🚨 ACİL BİLDİRİM - SAFETY MODE
        Ajan: Agent-{agent_id:03d}
        Hata Oranı: %{result.get('error_rate', 0):.2f}
        Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Ajan güvenli moda alındı. Müdahale gerekli!
        """
        logger.warning(message)
        
        # Dosyaya log yaz
        log_path = Path("safety_mode_logs")
        log_path.mkdir(exist_ok=True)
        log_file = log_path / f"safety_mode_{datetime.now().strftime('%Y%m%d')}.log"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} | {message}\n")
            f.write("-" * 60 + "\n")
    
    async def feedback_loop(self) -> None:
        """
        Geri besleme döngüsü - güncelleme sonrası ajan durumlarını kontrol eder
        """
        logger.info("🔄 Feedback Loop başlatılıyor...")
        
        # 10 saniye bekle
        await asyncio.sleep(10)
        
        for agent_id, config in self.agents.items():
            status = config.config.get("status", "unknown")
            if status == "updated":
                logger.debug(f"✅ Agent-{agent_id:03d} onaylandı.")
            elif status == "safety_mode":
                logger.warning(f"⚠️ Agent-{agent_id:03d} hala Safety Mode'da!")
    
    async def run(self) -> None:
        """Ana çalıştırma fonksiyonu"""
        logger.info("🚀 Update Protocol başlatılıyor...")
        
        await self.initialize_agents(200)
        summary = await self.update_all_agents()
        await self.feedback_loop()
        
        logger.info("✅ Update Protocol tamamlandı!")
        return summary

# ============================================================
# KOMUT SATIRI ÇALIŞTIRMA
# ============================================================

async def main():
    protocol = UpdateProtocol()
    result = await protocol.run()
    print("\n📊 SONUÇ ÖZETİ:")
    print(json.dumps(result, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())