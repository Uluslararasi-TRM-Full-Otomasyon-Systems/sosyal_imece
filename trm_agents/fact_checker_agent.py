# -*- coding: utf-8 -*-
"""
TRM Ticari Dünya - Kalkan Ajan Ordusu
Ajan: FactCheckerAgent
Amaç: Asılsız iddiaları resmi veri tabanı ve dernek tüzüğü ile çürütür.
Versiyon: 1.0.0
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.config_loader import load_config

class FactCheckerAgent:
    """
    FactCheckerAgent - Asılsız iddiaları resmi veri tabanı ve dernek tüzüğü ile çürütür.
    
    Bu ajan, TRM Ticari Ekosistem projesi hakkında yapılan asılsız iddiaları, yalan haberleri ve
    dezenformasyon içeriklerini resmi veri tabanı, dernek tüzüğü ve yasal belgeler ile
    karşılaştırarak doğruluğunu kontrol eder ve yanıltıcı bilgileri çürütür.
    """
    
    def __init__(self, agent_id=202):
        self.agent_id = agent_id
        self.name = f"FactCheckerAgent-{agent_id:03d}"
        self.config = load_config()
        self.status = "aktif"
        self.cpu_yuk = 0
        self.api_gecikme = 0
        
        # Resmi veri tabanı (simülasyon)
        self.resmi_veri_tabani = {
            "dernek_adi": "UTEYKDER",
            "dernek_tuzugu": "resmi_tuzuk_2024.pdf",
            "kayit_no": "34-12345",
            "mudurluk": "İstanbul Valiliği",
            "kurulus_tarihi": "2020-01-15",
            "amaci": "Sosyal dayanışma ve refah kültürünü yaşatmak",
            "faaliyet_alani": "Sosyal yardım, eğitim, kültür",
            "yuksek_kurul": "Yönetim Kurulu",
            "denetim": "Bağımsız denetim",
            "baskan": "M. Fahri Güzel"
        }
        
        # Yaygın asılsız iddialar ve yanıtları
        self.asilsiz_iddialar = {
            "dolandiricilik": {
                "id": "TRM Ticari Ekosistem bir dolandırıcılık şemasıdır",
                "yanit": "YANLIŞ. TRM Ticari Ekosistem, UTEYKDER derneği tarafından resmi olarak kayıtlı ve denetlenen bir sosyal sorumluluk projesidir. Kayıt No: 34-12345, İstanbul Valiliği",
                "kaynak": "Dernek Kayıt Belgesi"
            },
            "para_cebirme": {
                "id": "İnsanlardan para zorla alıyorlar",
                "yanit": "YANLIŞ. TRM Ticari Ekosistem tamamen gönüllülük esasına dayanır. Hiçbir zorlama veya baskı yapılmaz. Katılım tamamen özgür iradeye dayalıdır.",
                "kaynak": "Dernek Tüzüğü Madde 5"
            },
            "kara_para": {
                "id": "Kara para aklama faaliyeti yürütüyorlar",
                "yanit": "YANLIŞ. TRM Ticari Ekosistem tamamen şeffaf ve yasal faaliyetler yürütür. Tüm finansal işlemler bağımsız denetime tabidir ve Maliye uyumludur.",
                "kaynak": "Bağımsız Denetim Raporu 2024"
            },
            "gercek_degil": {
                "id": "Bu proje gerçek değil, hayal ürünü",
                "yanit": "YANLIŞ. TRM Ticari Ekosistem, UTEYKDER ve İŞADER dernekleri tarafından resmi olarak desteklenen, 200+ yapay zeka ajanı ile çalışan gerçek bir projedir.",
                "kaynak": "Dernek Resmi Web Sitesi"
            },
            "hileli_sistem": {
                "id": "Sistem hileli ve manipülatif",
                "yanit": "YANLIŞ. Sistem tamamen şeffaf ve denetlenebilir. Tüm ajan faaliyetleri loglanır ve raporlanır. Kod açık kaynak özelliklidir.",
                "kaynak": "Sistem Teknik Dokümantasyonu"
            }
        }
        
        self.log_dosyasi = os.path.join("logs", f"fact_checker_{agent_id}.log")
        self.setup_logging()
        self.log(f"🔍 {self.name} başlatılıyor...", "INFO")
        self.log(f"📚 Resmi veri tabanı yüklendi: {len(self.resmi_veri_tabani)} kayıt", "INFO")
        self.log(f"🚫 Asılsız iddia veritabanı yüklendi: {len(self.asilsiz_iddialar)} kayıt", "INFO")
    
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
    
    def iddia_kontrol_et(self, iddia: str) -> Dict[str, Any]:
        """
        Bir iddiayı resmi veri tabanı ile kontrol eder.
        
        Args:
            iddia: Kontrol edilecek iddia metni
            
        Returns:
            Dict: Kontrol sonucu
        """
        iddia_lower = iddia.lower()
        sonuc = {
            "iddia": iddia,
            "dogruluk_durumu": "bilinmiyor",
            "yanit": "",
            "kaynak": "",
            "kontrol_zamani": datetime.now().isoformat(),
            "güven_skoru": 0
        }
        
        # Asılsız iddialar veritabanında ara
        for kategori, veri in self.asilsiz_iddialar.items():
            if veri["id"].lower() in iddia_lower or any(kelime in iddia_lower for kelime in kategori.split("_")):
                sonuc["dogruluk_durumu"] = "YANLIŞ"
                sonuc["yanit"] = veri["yanit"]
                sonuc["kaynak"] = veri["kaynak"]
                sonuc["güven_skoru"] = 95
                self.log(f"❌ Asılsız iddia tespit edildi: {iddia[:50]}...", "WARNING")
                return sonuc
        
        # Resmi veri tabanı ile karşılaştır
        for anahtar, deger in self.resmi_veri_tabani.items():
            if str(deger).lower() in iddia_lower:
                sonuc["dogruluk_durumu"] = "DOĞRU"
                sonuc["yanit"] = f"Bilgi doğrudur. {anahtar}: {deger}"
                sonuc["kaynak"] = "Resmi Veri Tabanı"
                sonuc["güven_skoru"] = 90
                self.log(f"✅ Doğru bilgi tespit edildi: {iddia[:50]}...", "INFO")
                return sonuc
        
        # Bilinmeyen iddia
        sonuc["dogruluk_durumu"] = "DOĞRULANAMADI"
        sonuc["yanit"] = "Bu iddia hakkında yeterli bilgi bulunamadı. Daha fazla inceleme gerekiyor."
        sonuc["kaynak"] = "Manuel İnceleme Gerekli"
        sonuc["güven_skoru"] = 30
        self.log(f"❓ Bilinmeyen iddia: {iddia[:50]}...", "DEBUG")
        
        return sonuc
    
    def toplu_iddia_kontrol(self, iddialar: List[str]) -> List[Dict[str, Any]]:
        """
        Birden fazla iddiayı toplu olarak kontrol eder.
        
        Args:
            iddialar: Kontrol edilecek iddialar listesi
            
        Returns:
            List[Dict]: Kontrol sonuçları
        """
        sonuclar = []
        for iddia in iddialar:
            sonuc = self.iddia_kontrol_et(iddia)
            sonuclar.append(sonuc)
        return sonuclar
    
    def dogrulama_raporu_olustur(self, sonuclar: List[Dict[str, Any]]) -> str:
        """
        Doğrulama sonuçlarını raporlar.
        
        Args:
            sonuclar: Kontrol sonuçları
            
        Returns:
            str: Rapor dosyası yolu
        """
        rapor_dosyasi = os.path.join("reports", f"fact_checker_rapor_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        os.makedirs("reports", exist_ok=True)
        
        rapor = {
            "rapor_tarihi": datetime.now().isoformat(),
            "ajan_id": self.agent_id,
            "ajan_adi": self.name,
            "toplam_iddia": len(sonuclar),
            "dogru": len([s for s in sonuclar if s["dogruluk_durumu"] == "DOĞRU"]),
            "yanlis": len([s for s in sonuclar if s["dogruluk_durumu"] == "YANLIŞ"]),
            "dogrulanamadi": len([s for s in sonuclar if s["dogruluk_durumu"] == "DOĞRULANAMADI"]),
            "sonuclar": sonuclar,
            "ozet": {
                "en_yuksek_guven_skoru": max([s["güven_skoru"] for s in sonuclar]) if sonuclar else 0,
                "ortalama_guven_skoru": sum([s["güven_skoru"] for s in sonuclar]) / len(sonuclar) if sonuclar else 0
            }
        }
        
        with open(rapor_dosyasi, "w", encoding="utf-8") as f:
            json.dump(rapor, f, indent=4, ensure_ascii=False)
        
        self.log(f"📊 Doğrulama raporu oluşturuldu: {rapor_dosyasi}", "INFO")
        return rapor_dosyasi
    
    def dernek_tuzugu_kontrol(self, madde_no: int) -> Dict[str, Any]:
        """
        Dernek tüzüğünden belirli bir maddeyi kontrol eder.
        
        Args:
            madde_no: Kontrol edilecek madde numarası
            
        Returns:
            Dict: Madde içeriği
        """
        # Simülasyon - Gerçek tüzük dosyası okunmalı
        tuzuk_maddeleri = {
            1: "Derneğin Adı: UTEYKDER - Ulusal Türk Eğitim ve Yardımlaşma Derneği",
            2: "Merkez: İstanbul",
            3: "Amaç: Sosyal dayanışma ve refah kültürünü yaşatmak",
            4: "Çalışma Alanı: Sosyal yardım, eğitim, kültür",
            5: "Üyelik: Gönüllülük esasına dayalıdır"
        }
        
        madde = tuzuk_maddeleri.get(madde_no, "Madde bulunamadı")
        
        sonuc = {
            "madde_no": madde_no,
            "icerik": madde,
            "kaynak": "Dernek Tüzüğü",
            "kontrol_zamani": datetime.now().isoformat()
        }
        
        self.log(f"📖 Tüzük madde {madde_no} kontrol edildi", "INFO")
        return sonuc
    
    def run(self):
        """Ajanın ana çalışma döngüsü."""
        self.refresh_config()
        self.log(f"🔍 {self.name} çalışmaya başladı", "INFO")
        
        try:
            # Simüle edilmiş iddialar
            test_iddialar = [
                "TRM Ticari Ekosistem bir dolandırıcılık şemasıdır",
                "UTEYKDER resmi bir dernektir",
                "İnsanlardan para zorla alıyorlar",
                "Proje gerçek ve çalışıyor"
            ]
            
            # İddiaları kontrol et
            sonuclar = self.toplu_iddia_kontrol(test_iddialar)
            
            # Raporla
            rapor_dosyasi = self.dogrulama_raporu_olustur(sonuclar)
            self.log(f"✅ {len(sonuclar)} iddia kontrol edildi ve raporlandı", "INFO")
            
            # CPU ve API simülasyonu
            self.cpu_yuk = 20 + (len(sonuclar) * 3)
            self.api_gecikme = 90 + (len(sonuclar) * 8)
            
            self.log(f"⚡ CPU Yükü: {self.cpu_yuk}%, API Gecikme: {self.api_gecikme}ms", "INFO")
            
        except Exception as e:
            self.log(f"❌ Hata oluştu: {e}", "ERROR")
            self.cpu_yuk = 0
            self.api_gecikme = 0
