
import random
import time

def random_delay(min_sec=5, max_sec=60):
    time.sleep(random.uniform(min_sec, max_sec))

def get_user_agent():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0"
    ])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistem Muhafız Ajanı - TRM Otonom Ekosistemi
7/24 Sistem Gözetimi ve Otomatik Kurtarma
"""

import os
import time
import logging
import requests
import subprocess
import sys
from datetime import datetime
from threading import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SistemMuhafizAjani:
    """Sistem muhafız ajanı - 7/24 gözetim ve otomatik kurtarma"""
    
    def __init__(self):
        self.nobet_defteri = "muhafiz_nobet_defteri.txt"
        self.proje_koku = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.panel_url = "http://localhost:5000/api/saglik"
        self.kontrol_araligi = 30  # saniye
        self.panel_dosyasi = "api_server_2.py"
        self.calisiyor = False
        self.muhafiz_thread = None
    
    def nobet_girisi_yaz(self, mesaj):
        """Nöbet defterine giriş yaz"""
        try:
            zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.nobet_defteri, 'a', encoding='utf-8') as f:
                f.write(f"[{zaman}] {mesaj}\n")
            logger.info(f"Nöbet defterine yazıldı: {mesaj}")
        except Exception as e:
            logger.error(f"Nöbet defteri yazma hatası: {e}")
    
    def nobet_kayitlarini_oku(self):
        """Nöbet kayıtlarını oku"""
        try:
            if not os.path.exists(self.nobet_defteri):
                return []
            
            with open(self.nobet_defteri, 'r', encoding='utf-8') as f:
                kayitlar = f.readlines()
            
            return kayitlar[-50:]  # Son 50 kayıt
        except Exception as e:
            logger.error(f"Nöbet kayıtları okuma hatası: {e}")
            return []
    
    def sunucu_kontrol(self):
        """API sunucusunun durumunu kontrol et"""
        try:
            response = requests.get(self.panel_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Sunucu kontrol hatası: {e}")
            return False
    
    def sunucu_baslat(self):
        """API sunucusunu başlat"""
        try:
            self.nobet_girisi_yaz("⚠️ SUNUCU ÇÖKTÜ! Otomatik kurtarma başlatılıyor...")
            
            subprocess.Popen(
                [sys.executable, self.panel_dosyasi],
                cwd=self.proje_koku,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            self.nobet_girisi_yaz("✅ SUNUCU BAŞLATILDI! Kurtarma başarılı.")
            return True
        except Exception as e:
            self.nobet_girisi_yaz(f"❌ SUNUCU BAŞLATMA HATASI: {str(e)}")
            logger.error(f"Sunucu başlatma hatası: {e}")
            return False
    
    def muhafiz_gorevi(self):
        """Muhafız görevi döngüsü"""
        self.nobet_girisi_yaz("🐾 SİSTEM MUHAFIZI NÖBET BAŞLADI! 7/24 Gözetim aktif.")
        
        while self.calisiyor:
            try:
                # Sunucu kontrolü
                sunucu_aktif = self.sunucu_kontrol()
                
                if sunucu_aktif:
                    self.nobet_girisi_yaz("✅ Sunucu aktif ve sağlıklı.")
                else:
                    self.nobet_girisi_yaz("❌ Sunucu çöktü! Kurtarma başlatılıyor...")
                    self.sunucu_baslat()
                    time.sleep(10)  # Sunucunun başlaması için bekle
                
            except Exception as e:
                self.nobet_girisi_yaz(f"⚠️ Görev hatası: {str(e)}")
            
            time.sleep(self.kontrol_araligi)
        
        self.nobet_girisi_yaz("🐾 SİSTEM MUHAFIZI NÖBET BİTTİ!")
    
    def muhafizi_baslat(self):
        """Muhafız ajanını başlat"""
        if not self.calisiyor:
            self.calisiyor = True
            self.muhafiz_thread = Thread(target=self.muhafiz_gorevi, daemon=True)
            self.muhafiz_thread.start()
            logger.info("Sistem muhafızı başlatıldı")
            return True
        return False
    
    def muhafizi_durdur(self):
        """Muhafız ajanını durdur"""
        if self.calisiyor:
            self.calisiyor = False
            if self.muhafiz_thread:
                self.muhafiz_thread.join(timeout=5)
            logger.info("Sistem muhafızı durduruldu")
            return True
        return False
    
    def sistem_durumu_raporu(self):
        """Sistem durum raporu oluştur"""
        sunucu_aktif = self.sunucu_kontrol()
        return {
            "sunucu_durumu": "AKTİF" if sunucu_aktif else "ÇÖKÜK",
            "muhafiz_durumu": "AKTİF" if self.calisiyor else "PASİF",
            "kontrol_araligi": f"{self.kontrol_araligi} saniye",
            "nobet_kayit_sayisi": len(self.nobet_kayitlarini_oku())
        }

if __name__ == "__main__":
    # Muhafızı bağımsız çalıştır
    muhafiz = SistemMuhafizAjani()
    muhafiz.muhafizi_baslat()
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        muhafiz.muhafizi_durdur()
        print("Muhafız durduruldu.")
