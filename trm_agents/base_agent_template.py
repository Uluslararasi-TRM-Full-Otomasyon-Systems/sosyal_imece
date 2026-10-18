#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TRM Ticari Dünya - Base Agent Şablonu (TRM Agents)
Versiyon: 3.0.0

Tüm ajanlar bu sınıftan türetilmelidir.
Bu dosya: trm_agents/base_agent_template.py
"""

import os
import sys
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod

# Sistem ana dizinini bul
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "global_config.json")

# ============================================
# BASE AGENT SINIFI
# ============================================

class BaseAgent(ABC):
    """
    Tüm ajanlar için temel sınıf.
    Her ajan bu sınıftan türetilmeli ve gerekli metodları implement etmelidir.
    """
    
    def __init__(self, agent_name: str = "BaseAgent", agent_id: Optional[int] = None):
        """
        BaseAgent başlatıcısı
        
        Args:
            agent_name: Ajanın adı
            agent_id: Ajan ID'si (opsiyonel)
        """
        self.agent_name = agent_name
        self.agent_id = agent_id
        self.status = "initializing"
        self.created_at = datetime.now().isoformat()
        self.last_heartbeat = None
        self.is_running = False
        self.is_active = True  # Health check için aktiflik durumu
        self.heartbeat_interval = 30  # saniye
        self.heartbeat_thread = None
        
        # Logging once kurulmali; load_config log kullanir
        self.setup_logging()
        self.config = self.load_config()
        
        self.log(f"🚀 {self.agent_name} başlatılıyor...", "INFO")
        self.log(f"📁 Agent ID: {self.agent_id}", "INFO")
        self.status = "ready"
    
    # ============================================
    # YAPILANDIRMA METODLARI
    # ============================================
    
    def load_config(self) -> Dict[str, Any]:
        """
        global_config.json dosyasını yükler.
        Dosya yoksa veya okunamazsa varsayılan değerleri döndürür.
        """
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.log("✅ global_config.json başarıyla yüklendi", "INFO")
                    return config
            else:
                self.log(f"⚠️ global_config.json bulunamadı: {CONFIG_PATH}", "WARNING")
                return {}
        except json.JSONDecodeError as e:
            self.log(f"❌ JSON ayrıştırma hatası: {e}", "ERROR")
            return {}
        except Exception as e:
            self.log(f"❌ Config yükleme hatası: {e}", "ERROR")
            return {}
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Config'ten belirtilen anahtarın değerini döndürür.
        Nokta ile ayrılmış anahtar destekler (örn: "social_media.default_video")
        """
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value.get(k, {})
                if not isinstance(value, dict):
                    return value if value is not None else default
            return value if value is not None else default
        except:
            return default
    
    def setup_logging(self) -> None:
        """Logging sistemini kurar"""
        log_dir = os.path.join(BASE_DIR, "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, f"{self.agent_name.lower().replace(' ', '_')}.log")
        
        stream_handler = logging.StreamHandler(sys.stdout)
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

        logging.basicConfig(
            level=logging.INFO,
            format=f'[%(asctime)s] [%(name)s] %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                stream_handler,
            ],
            force=True,
        )
        self.logger = logging.getLogger(self.agent_name)
    
    def log(self, message: str, level: str = "INFO") -> None:
        """
        Ajan log mesajı gönderir
        
        Args:
            message: Log mesajı
            level: Log seviyesi (INFO, WARNING, ERROR, DEBUG)
        """
        if hasattr(self, 'logger'):
            log_methods = {
                "INFO": self.logger.info,
                "WARNING": self.logger.warning,
                "ERROR": self.logger.error,
                "DEBUG": self.logger.debug
            }
            method = log_methods.get(level.upper(), self.logger.info)
            method(message)
        else:
            print(f"[{level}] [{self.agent_name}] {message}")
    
    # ============================================
    # AJAN KONTROL METODLARI
    # ============================================
    
    def set_agent_id(self, agent_id: int) -> None:
        """Ajan ID'sini ayarlar"""
        self.agent_id = agent_id
        self.log(f"🔑 Agent ID ayarlandı: {agent_id}", "INFO")
    
    def get_agent_id(self) -> Optional[int]:
        """Ajan ID'sini döndürür"""
        return self.agent_id
    
    def get_status(self) -> Dict[str, Any]:
        """
        Ajan durumunu döndürür
        
        Returns:
            Ajan durum bilgileri
        """
        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "status": self.status,
            "created_at": self.created_at,
            "last_heartbeat": self.last_heartbeat,
            "is_running": self.is_running
        }
    
    def get_heartbeat(self) -> Dict[str, Any]:
        """
        Heartbeat mesajı üretir
        
        Returns:
            Heartbeat verileri
        """
        self.last_heartbeat = datetime.now().isoformat()
        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "status": self.status,
            "timestamp": self.last_heartbeat,
            "uptime": self.get_uptime()
        }
    
    def get_uptime(self) -> str:
        """Çalışma süresini döndürür"""
        if self.created_at:
            start = datetime.fromisoformat(self.created_at)
            delta = datetime.now() - start
            seconds = delta.total_seconds()
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}h {minutes}m {secs}s"
        return "0s"
    
    # ============================================
    # HEARTBEAT THREAD
    # ============================================
    
    def start_heartbeat(self) -> None:
        """Heartbeat thread'ini başlatır"""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.log("⚠️ Heartbeat zaten çalışıyor", "WARNING")
            return
        
        self.is_running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        self.log("💓 Heartbeat thread başlatıldı", "INFO")
    
    def stop_heartbeat(self) -> None:
        """Heartbeat thread'ini durdurur"""
        self.is_running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        self.log("💓 Heartbeat thread durduruldu", "INFO")
    
    def _heartbeat_loop(self) -> None:
        """Heartbeat döngüsü"""
        while self.is_running:
            try:
                heartbeat_data = self.get_heartbeat()
                self.log(f"💓 Heartbeat: {heartbeat_data['status']}", "DEBUG")
                self.on_heartbeat(heartbeat_data)
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                self.log(f"❌ Heartbeat hatası: {e}", "ERROR")
                time.sleep(5)
    
    def on_heartbeat(self, heartbeat_data: Dict[str, Any]) -> None:
        """
        Heartbeat olayı için override edilebilir metod.
        Alt sınıflar bu metodu kendi ihtiyaçlarına göre implement edebilir.
        """
        pass
    
    # ============================================
    # ANA METODLAR (ABSTRACT)
    # ============================================
    
    @abstractmethod
    def run(self, **kwargs) -> Any:
        """
        Ana çalıştırma metodu.
        Alt sınıflar tarafından ZORUNLU olarak implement edilmelidir.
        
        Raises:
            NotImplementedError: Alt sınıf bu metodu implement etmemişse
        """
        raise NotImplementedError(f"{self.agent_name}: run() metodu implement edilmemiş!")
    
    @abstractmethod
    def stop(self) -> None:
        """
        Ajanı durdurur.
        Alt sınıflar tarafından ZORUNLU olarak implement edilmelidir.
        """
        raise NotImplementedError(f"{self.agent_name}: stop() metodu implement edilmemiş!")
    
    @abstractmethod
    def restart(self) -> None:
        """
        Ajanı yeniden başlatır.
        Alt sınıflar tarafından ZORUNLU olarak implement edilmelidir.
        """
        raise NotImplementedError(f"{self.agent_name}: restart() metodu implement edilmemiş!")
    
    # ============================================
    # YARDIMCI METODLAR
    # ============================================
    
    def save_state(self, state: Dict[str, Any], state_file: str = None) -> bool:
        """
        Ajan durumunu dosyaya kaydeder
        
        Args:
            state: Kaydedilecek durum verileri
            state_file: Durum dosyası yolu (opsiyonel)
        
        Returns:
            Başarılı ise True
        """
        try:
            if state_file is None:
                state_dir = os.path.join(BASE_DIR, "data", "agent_states")
                if not os.path.exists(state_dir):
                    os.makedirs(state_dir)
                state_file = os.path.join(state_dir, f"{self.agent_name.lower().replace(' ', '_')}_state.json")
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.log(f"❌ Durum kaydetme hatası: {e}", "ERROR")
            return False
    
    def load_state(self, state_file: str = None) -> Dict[str, Any]:
        """
        Ajan durumunu dosyadan yükler
        
        Args:
            state_file: Durum dosyası yolu (opsiyonel)
        
        Returns:
            Yüklenen durum verileri
        """
        try:
            if state_file is None:
                state_dir = os.path.join(BASE_DIR, "data", "agent_states")
                state_file = os.path.join(state_dir, f"{self.agent_name.lower().replace(' ', '_')}_state.json")
            
            if os.path.exists(state_file):
                with open(state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.log(f"❌ Durum yükleme hatası: {e}", "ERROR")
            return {}
    
    def __str__(self) -> str:
        return f"{self.agent_name} (ID: {self.agent_id}, Status: {self.status})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.agent_name} (ID: {self.agent_id})>"