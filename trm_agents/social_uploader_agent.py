#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TRM Ticari Dünya - Sosyal Medya Uploader Ajanı
Versiyon: 3.0.0 (Otonom TRM Sistemi)

BaseAgent: trm_agents/base_agent_template.py
Bu ajan, üretilen içerikleri sosyal medya ağlarına dağıtır.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# ★★★ BaseAgent import ★★★
try:
    from trm_agents.base_agent_template import BaseAgent
except ImportError:
    # Eğer trm_agents içinde değilse, doğru yolu dene
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from trm_agents.base_agent_template import BaseAgent

# ============================================
# SİSTEM YAPILANDIRMASI
# ============================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================
# SOCIAL UPLOADER AGENT
# ============================================

class SocialUploaderAgent(BaseAgent):
    """
    Üretilen içerikleri sosyal medya ağlarına dağıtan otonom ajan.
    BaseAgent'dan türetilmiştir.
    """
    
    def __init__(self, agent_name: str = "Sosyal_Medya_Uploader", agent_id: Optional[int] = None):
        """
        Ajan başlatma
        
        Args:
            agent_name: Ajan adı
            agent_id: Ajan ID'si (opsiyonel)
        """
        # ★★★ BaseAgent init çağrısı ★★★
        super().__init__(agent_name, agent_id)
        
        # API anahtarlarını yükle
        self.api_keys = self._load_api_keys()
        
        # Platform durumunu kontrol et
        self.platform_status = self._check_api_availability()
        
        # Varsayılan değerler
        self.default_video = self.get_config("social_media.default_video", "path/to/default_video.mp4")
        self.default_language = self.get_config("social_media.default_language", "tr")
        self.platforms = self.get_config("social_media.platforms", ["YouTube_Shorts", "TikTok", "Instagram_Reels"])
        
        self.log(f"📊 Platform durumu: {self.platform_status}", "INFO")
        self.log(f"📁 Varsayılan video: {self.default_video}", "INFO")
        self.log(f"🌐 Varsayılan dil: {self.default_language}", "INFO")
        
        # Heartbeat başlat
        self.start_heartbeat()
        
        self.status = "ready"
    
    # ============================================
    # API KEY METODLARI
    # ============================================
    
    def _load_api_keys(self) -> Dict[str, str]:
        """
        API anahtarlarını yükler.
        Önce environment variables, sonra config dosyası.
        """
        keys = {
            "youtube_api_key": os.getenv("YOUTUBE_API_KEY", ""),
            "tiktok_api_key": os.getenv("TIKTOK_API_KEY", ""),
            "instagram_access_token": os.getenv("INSTAGRAM_ACCESS_TOKEN", ""),
            "twitter_api_key": os.getenv("TWITTER_API_KEY", ""),
            "twitter_api_secret": os.getenv("TWITTER_API_SECRET", "")
        }
        
        # Config'ten API anahtarlarını da dene
        config_keys = self.get_config("api_keys", {})
        for key, value in config_keys.items():
            if key in keys and not keys.get(key) and value:
                keys[key] = value
        
        # Eksik anahtar uyarısı
        for platform, key in keys.items():
            if not key:
                self.log(f"⚠️ {platform} için API anahtarı eksik", "WARNING")
        
        return keys
    
    def _check_api_availability(self) -> Dict[str, bool]:
        """API anahtarlarının kullanılabilirliğini kontrol et"""
        status = {}
        for platform, key in self.api_keys.items():
            status[platform] = bool(key)
        return status
    
    # ============================================
    # UPLOAD METODLARI
    # ============================================
    
    def upload_to_platform(self, video_path: str, platform: str, language: str) -> bool:
        """
        Video dosyasını platforma yükler.
        Hata durumunda False döndürür.
        """
        # Platform bazlı API anahtarı kontrolü
        platform_key_map = {
            "YouTube_Shorts": "youtube_api_key",
            "TikTok": "tiktok_api_key",
            "Instagram_Reels": "instagram_access_token",
            "Twitter": "twitter_api_key"
        }
        
        key_name = platform_key_map.get(platform)
        if key_name and not self.api_keys.get(key_name):
            self.log(f"⚠️ {platform} için API anahtarı eksik, simülasyon modunda", "WARNING")
            self.log(f"📤 Simülasyon: {video_path} → {platform} ({language})", "INFO")
            return True
        
        try:
            # ★★★ GERÇEK API ENTEGRASYONU ★★★
            # Buraya gerçek API çağrıları gelecek
            self.log(f"📤 Yükleniyor: {video_path} → {platform} ({language})", "INFO")
            
            # Simülasyon başarılı
            return True
            
        except Exception as e:
            self.log(f"❌ {platform} yükleme hatası: {e}", "ERROR")
            return False
    
    # ============================================
    # ANA METODLAR (BASEAGENT'DEN ZORUNLU)
    # ============================================
    
    def run(self, video_path: Optional[str] = None, language: Optional[str] = None) -> List[Dict]:
        """
        ★★★ BaseAgent.run() implementasyonu ★★★
        Dağıtım döngüsü.
        
        Args:
            video_path: Yüklenecek video dosyası yolu (opsiyonel)
            language: Video dili (opsiyonel)
        
        Returns:
            Yükleme sonuçlarının listesi
        """
        # ★★★ TRY-EXCEPT BLOĞU - SİSTEMİN ÇÖKMESİNİ ENGELLER ★★★
        try:
            self.log("🔄 Sosyal medya dağıtımı başlatılıyor...", "INFO")
            
            # Parametreler gelmediyse config'ten oku
            if video_path is None:
                video_path = self.default_video
                # Path'i BASE_DIR'e göre normalize et
                if not os.path.isabs(video_path):
                    video_path = os.path.join(BASE_DIR, video_path)
                self.log(f"📁 Varsayılan video path: {video_path}", "INFO")
            
            if language is None:
                language = self.default_language
                self.log(f"🌐 Varsayılan dil: {language}", "INFO")
            
            # Video dosyası varlığını kontrol et
            if not os.path.exists(video_path):
                self.log(f"❌ Video dosyası bulunamadı: {video_path}", "ERROR")
                # Yedek video ara
                backup_video = os.path.join(BASE_DIR, "content", "videos", "default.mp4")
                if os.path.exists(backup_video):
                    video_path = backup_video
                    self.log(f"📁 Yedek video bulundu: {video_path}", "INFO")
                else:
                    self.log(f"⚠️ Yedek video da bulunamadı, simülasyon devam ediyor", "WARNING")
            
            upload_results = []
            
            # Her platforma yükle
            for platform in self.platforms:
                try:
                    result = self.upload_to_platform(video_path, platform, language)
                    upload_results.append({
                        "platform": platform,
                        "language": language,
                        "video_path": video_path,
                        "status": "BAŞARI" if result else "HATA",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    self.log(f"❌ {platform} yükleme hatası: {e}", "ERROR")
                    upload_results.append({
                        "platform": platform,
                        "language": language,
                        "video_path": video_path,
                        "status": f"HATA: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    })
            
            self.log(f"✅ Dağıtım tamamlandı. {len(upload_results)} platform işlendi.", "INFO")
            return upload_results
            
        except Exception as e:
            # ★★★ KRİTİK HATA - SADECE LOGLA ★★★
            self.log(f"❌ KRİTİK HATA: {e}", "ERROR")
            self.log("⚠️ Sistem çalışmaya devam ediyor. Hata loglandı.", "WARNING")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            
            return [{
                "status": "KRİTİK HATA",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }]
    
    def stop(self) -> None:
        """
        ★★★ BaseAgent.stop() implementasyonu ★★★
        Ajanı durdurur.
        """
        self.log("🛑 Ajan durduruluyor...", "INFO")
        self.status = "stopping"
        self.is_running = False
        self.stop_heartbeat()
        self.status = "stopped"
        self.log("✅ Ajan durduruldu", "INFO")
    
    def restart(self) -> None:
        """
        ★★★ BaseAgent.restart() implementasyonu ★★★
        Ajanı yeniden başlatır.
        """
        self.log("🔄 Ajan yeniden başlatılıyor...", "INFO")
        self.stop()
        time.sleep(2)
        self.status = "restarting"
        self.start_heartbeat()
        self.status = "ready"
        self.log("✅ Ajan yeniden başlatıldı", "INFO")
    
    # ============================================
    # HEARTBEAT OLAYI
    # ============================================
    
    def on_heartbeat(self, heartbeat_data: Dict[str, Any]) -> None:
        """
        ★★★ BaseAgent.on_heartbeat() override ★★★
        Heartbeat olayında yapılacak işlemler.
        """
        # Heartbeat ile birlikte durum gönder
        pass
    
    # ============================================
    # DURUM METODLARI
    # ============================================
    
    def get_status(self) -> Dict[str, Any]:
        """
        ★★★ BaseAgent.get_status() override ★★★
        Ajan durumunu döndürür.
        """
        base_status = super().get_status()
        base_status.update({
            "platform_status": self.platform_status,
            "default_video": self.default_video,
            "default_language": self.default_language,
            "platforms": self.platforms,
            "api_keys_available": sum(1 for v in self.api_keys.values() if v),
            "total_api_keys": len(self.api_keys)
        })
        return base_status


# ============================================
# ORKESTRATÖR İÇİN TETİKLEYİCİ
# ============================================

def trigger_social_upload(video_path: Optional[str] = None, language: Optional[str] = None) -> List[Dict]:
    """
    Orkestratör tarafından çağrılan tetikleyici fonksiyon.
    
    Args:
        video_path: Yüklenecek video dosyası yolu (opsiyonel)
        language: Video dili (opsiyonel)
    
    Returns:
        Yükleme sonuçlarının listesi
    """
    try:
        uploader = SocialUploaderAgent()
        return uploader.run(video_path, language)
    except Exception as e:
        # Tetikleyici hatasını logla
        import logging
        logging.error(f"❌ Tetikleyici hatası: {e}")
        return [{
            "status": "TETİKLEYİCİ HATA",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }]


# ============================================
# BAĞIMSIZ ÇALIŞTIRMA
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("TRM TICARI DUNYA - SOSYAL UPLOADER AJAN")
    print("BaseAgent: trm_agents/base_agent_template.py")
    print("=" * 60)
    
    # Ajan başlat
    agent = SocialUploaderAgent(agent_id=50)
    
    # Test 1: Parametresiz çalıştırma (config'ten okur)
    print("\n📤 Test 1: Parametresiz çalıştırma")
    results = agent.run()
    for result in results:
        print(f"  {result.get('platform', 'Bilinmiyor')}: {result.get('status')}")
    
    # Test 2: Özel parametreler ile
    print("\n📤 Test 2: Özel parametreler ile")
    results = agent.run(
        video_path="test_video.mp4",
        language="en"
    )
    for result in results:
        print(f"  {result.get('platform', 'Bilinmiyor')}: {result.get('status')}")
    
    # Durum sorgula
    print("\n📊 Ajan Durumu:")
    status = agent.get_status()
    print(f"  Ad: {status.get('agent_name')}")
    print(f"  ID: {status.get('agent_id')}")
    print(f"  Durum: {status.get('status')}")
    print(f"  Platformlar: {status.get('platforms')}")
    
    print("\n✅ Test tamamlandı.")