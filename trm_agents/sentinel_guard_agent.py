# -*- coding: utf-8 -*-
"""
TRM Ticari Dünya - Kalkan Ajan Ordusu
Ajan: SentinelGuardAgent
Amaç: Sosyal medya ve ağlardaki dezenformasyonu/karalamaları izler.
Versiyon: 1.0.0
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.config_loader import load_config

class SentinelGuardAgent:
    """
    SentinelGuardAgent - Sosyal medya ve ağlardaki dezenformasyonu/karalamaları izler.
    
    Bu ajan, sosyal medya platformları, forumlar ve web sitelerinde TRM Ticari Ekosistem projesi
    hakkında yapılan olumsuz, yanlış veya kötü niyetli içerikleri otomatik olarak izler,
    analiz eder ve raporlar.
    """
    
    def __init__(self, agent_id=201):
        self.agent_id = agent_id
        self.name = f"SentinelGuardAgent-{agent_id:03d}"
        self.config = load_config()
        self.status = "aktif"
        self.cpu_yuk = 0
        self.api_gecikme = 0
        self.izlenen_platformlar = [
            "twitter", "facebook", "instagram", "youtube", 
            "reddit", "linkedin", "tiktok", "telegram"
        ]
        self.izlenen_anahtar_kelimeler = [
            "trm ticari ekosistem", "uteykder", "işader", "ir-sa", "m. fahri güzel",
            "trm", "nirvana", "kuresel ticari"
        ]
        self.negatif_ifadeler = [
            "dolandırıcılık", "sahte", "kandırma", "yalan", "ifşa", 
            "skandal", "kara para", "suç", "hile", "kumpas"
        ]
        self.tespit_edilen_threatler = []
        self.log_dosyasi = os.path.join("logs", f"sentinel_guard_{agent_id}.log")
        
        # Logging ayarla
        self.setup_logging()
        self.log(f"🛡️ {self.name} başlatılıyor...", "INFO")
        self.log(f"📡 İzlenen platformlar: {len(self.izlenen_platformlar)}", "INFO")
        self.log(f"🔑 İzlenen anahtar kelimeler: {len(self.izlenen_anahtar_kelimeler)}", "INFO")
    
    def setup_logging(self):
        """Logging sistemini kurar."""
        os.makedirs("logs", exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.log_dosyasi, encoding="utf-8"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.name)
    
    def log(self, mesaj: str, seviye: str = "INFO"):
        """Log mesajı yazar."""
        if seviye == "INFO":
            self.logger.info(mesaj)
        elif seviye == "WARNING":
            self.logger.warning(mesaj)
        elif seviye == "ERROR":
            self.logger.error(mesaj)
        elif seviye == "DEBUG":
            self.logger.debug(mesaj)
    
    def refresh_config(self):
        """Her döngüde güncel konfigürasyonu al."""
        self.config = load_config()
    
    def sosyal_medya_izle(self) -> List[Dict[str, Any]]:
        """
        Sosyal medya platformlarını izler ve tehditleri tespit eder.
        
        Returns:
            List[Dict]: Tespit edilen tehditlerin listesi
        """
        tehditler = []
        
        # Simülasyon - Gerçek API entegrasyonu gerektirir
        for platform in self.izlenen_platformlar:
            # Her platform için simüle edilmiş tarama
            platform_threat_sayisi = self.random_threat_sayisi()
            
            if platform_threat_sayisi > 0:
                for i in range(platform_threat_sayisi):
                    threat = {
                        "platform": platform,
                        "anahtar_kelime": self.izlenen_anahtar_kelimeler[i % len(self.izlenen_anahtar_kelimeler)],
                        "negatif_ifade": self.negatif_ifadeler[i % len(self.negatif_ifadeler)],
                        "tespit_zamani": datetime.now().isoformat(),
                        "tehlik_seviyesi": self.tehlik_seviyesi_hesapla(),
                        "kullanici_adi": f"anonim_{i}",
                        "icerik_url": f"https://{platform}.com/post/{i}",
                        "durum": "tespit_edildi"
                    }
                    tehditler.append(threat)
                    self.log(f"⚠️ {platform}'da tehdit tespit edildi: {threat['negatif_ifade']}", "WARNING")
        
        return tehditler
    
    def random_threat_sayisi(self) -> int:
        """Rastgele tehdit sayısı döndürür (simülasyon)."""
        import random
        return random.randint(0, 3)
    
    def tehlik_seviyesi_hesapla(self) -> str:
        """Tehlike seviyesini hesaplar."""
        import random
        seviyeler = ["düşük", "orta", "yüksek", "kritik"]
        return random.choice(seviyeler)
    
    def tehdit_analiz_et(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tespit edilen tehditi analiz eder.
        
        Args:
            threat: Tehdit bilgileri
            
        Returns:
            Dict: Analiz sonucu
        """
        analiz = {
            "threat_id": threat.get("tespit_zamani", ""),
            "platform": threat.get("platform", ""),
            "tehlik_seviyesi": threat.get("tehlik_seviyesi", "bilinmiyor"),
            "aksiyon_onerisi": self.aksiyon_onerisi_belirle(threat),
            "analiz_zamani": datetime.now().isoformat(),
            "durum": "analiz_edildi"
        }
        
        self.log(f"🔍 Tehdit analiz edildi: {analiz['aksiyon_onerisi']}", "INFO")
        return analiz
    
    def aksiyon_onerisi_belirle(self, threat: Dict[str, Any]) -> str:
        """Tehdit için aksiyon önerisi belirler."""
        seviye = threat.get("tehlik_seviyesi", "düşük")
        
        if seviye == "kritik":
            return "Acil yasal müdahale ve hukuki süreç başlatma"
        elif seviye == "yüksek":
            return "Resmi açıklama ve hukuki uyarı gönderme"
        elif seviye == "orta":
            return "İçerik raporlama ve platform bildirimi"
        else:
            return "İzleme ve takip etme"
    
    def tehdit_raporla(self, tehditler: List[Dict[str, Any]]) -> str:
        """
        Tespit edilen tehditleri raporlar.
        
        Args:
            tehditler: Tehdit listesi
            
        Returns:
            str: Rapor dosyası yolu
        """
        rapor_dosyasi = os.path.join("reports", f"sentinel_guard_rapor_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        os.makedirs("reports", exist_ok=True)
        
        rapor = {
            "rapor_tarihi": datetime.now().isoformat(),
            "ajan_id": self.agent_id,
            "ajan_adi": self.name,
            "toplam_threat": len(tehditler),
            "platformlar": list(set([t["platform"] for t in tehditler])),
            "tehditler": tehditler,
            "ozet": {
                "kritik": len([t for t in tehditler if t["tehlik_seviyesi"] == "kritik"]),
                "yüksek": len([t for t in tehditler if t["tehlik_seviyesi"] == "yüksek"]),
                "orta": len([t for t in tehditler if t["tehlik_seviyesi"] == "orta"]),
                "düşük": len([t for t in tehditler if t["tehlik_seviyesi"] == "düşük"])
            }
        }
        
        with open(rapor_dosyasi, "w", encoding="utf-8") as f:
            json.dump(rapor, f, indent=4, ensure_ascii=False)
        
        self.log(f"📊 Rapor oluşturuldu: {rapor_dosyasi}", "INFO")
        return rapor_dosyasi
    
    def run(self):
        """Ajanın ana çalışma döngüsü."""
        self.refresh_config()
        self.log(f"🛡️ {self.name} çalışmaya başladı", "INFO")
        
        try:
            # Sosyal medya izleme
            tehditler = self.sosyal_medya_izle()
            
            # Tehditleri analiz et
            analiz_edilenler = []
            for threat in tehditler:
                analiz = self.tehdit_analiz_et(threat)
                analiz_edilenler.append(analiz)
            
            # Raporla
            if tehditler:
                rapor_dosyasi = self.tehdit_raporla(tehditler)
                self.log(f"✅ {len(tehditler)} tehdit tespit edildi ve raporlandı", "INFO")
            else:
                self.log("✅ Tehdit tespit edilmedi", "INFO")
            
            # CPU ve API simülasyonu
            self.cpu_yuk = 15 + (len(tehditler) * 5)
            self.api_gecikme = 80 + (len(tehditler) * 10)
            
            self.log(f"⚡ CPU Yükü: {self.cpu_yuk}%, API Gecikme: {self.api_gecikme}ms", "INFO")
            
        except Exception as e:
            self.log(f"❌ Hata oluştu: {e}", "ERROR")
            self.cpu_yuk = 0
            self.api_gecikme = 0
