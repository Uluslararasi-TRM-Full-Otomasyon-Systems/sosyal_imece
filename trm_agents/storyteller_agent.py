# -*- coding: utf-8 -*-
"""
TRM Ticari Dünya - Küresel Anlatı Ajan Ordusu
Ajan: StorytellerAgent
Amaç: Dezavantajlı vatandaşların ilham verici hikayelerini merhamet diliyle aktarır.
Versiyon: 1.0.0
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.config_loader import load_config

class StorytellerAgent:
    """
    StorytellerAgent - Dezavantajlı vatandaşların ilham verici hikayelerini merhamet diliyle aktarır.
    
    Bu ajan, TRM Ticari Ekosistem projesinden faydalanan dezavantajlı vatandaşların gerçek hikayelerini
    toplar, işler ve merhamet dolu bir dille sosyal medya, web sitesi ve diğer platformlarda
    paylaşır. Bu hikayeler, projenin toplumsal etkisini gösterir ve ilham kaynağı olur.
    """
    
    def __init__(self, agent_id=204):
        self.agent_id = agent_id
        self.name = f"StorytellerAgent-{agent_id:03d}"
        self.config = load_config()
        self.status = "aktif"
        self.cpu_yuk = 0
        self.api_gecikme = 0
        
        # Hikaye veritabanı (simülasyon)
        self.hikaye_veritabani = [
            {
                "kisi_adi": "Ahmet Yılmaz",
                "durum": "Engelli birey",
                "onceki_durum": "İşsiz, gelir yok",
                "simdiki_durum": "Aylık 5.000 TL gelir, sosyal güvenlik",
                "hikaye": "TRM Ticari Ekosistem sayesinde hayatım değişti. Artık kendimi有用lı hissediyorum.",
                "tarih": "2024-01-15",
                "kategori": "engelli_destek"
            },
            {
                "kisi_adi": "Fatma Demir",
                "durum": "Tek ebeveyn",
                "onceki_durum": "Çocuklarıyla birlikte zorluk yaşıyordu",
                "simdiki_durum": "Düzenli gelir, çocukları okula gidiyor",
                "hikaye": "TRM Ticari Ekosistem bana umut verdi. Çocuklarımın geleceği için çalışabiliyorum.",
                "tarih": "2024-02-20",
                "kategori": "tek_ebeveyn"
            },
            {
                "kisi_adi": "Mehmet Kaya",
                "durum": "Yaşlı vatandaş",
                "onceki_durum": "Yalnız, maddi sıkıntı",
                "simdiki_durum": "Düzenli gelir, sosyal bağlantılar",
                "hikaye": "TRM Ticari Ekosistem sayesinde yalnız değilim. Topluluğun bir parçasıyım.",
                "tarih": "2024-03-10",
                "kategori": "yasli_destek"
            }
        ]
        
        # Merhamet dili şablonları
        self.merhamet_dili_sablonlari = {
            "baslik": "🌟 {kisi_adi}'ın Hikayesi: Umudun Işığı",
            "giris": """
Sevgili dostlarımız,

Bugün sizinle {kisi_adi}'ın ilham verici hikayesini paylaşmak istiyoruz. 
{durum} olan {kisi_adi}, TRM Ticari Ekosistem projesi sayesinde hayatında büyük bir 
değişim yaşadı. Bu hikaye, umudun ve dayanışmanın gücünü gösteriyor.
            """,
            "govde": """
📌 Önceki Durum:
{onceki_durum}

✨ Şimdiki Durum:
{simdiki_durum}

💬 {kisi_adi}'ın Sözleri:
"{hikaye}"

🤝 TRM Ticari Ekosistem olarak, {kisi_adi}'ın bu başarıya ulaşmasında küçük bir 
katkımız oldu. Bu başarı, hepimizin başarısıdır.
            """,
            "kapanis": """
Bu hikaye, TRM Ticari Ekosistem'nin toplumsal etkisinin küçük bir örneğidir.
Her gün, yüzlerce insanın hayatında olumlu değişim yaratıyoruz.

🌈 Dayanışma ile güçleniyoruz,
TRM Ticari Ekosistem Ekibi
            """
        }
        
        # Platform formatları
        self.platform_formatlari = {
            "twitter": {
                "max_karakter": 280,
                "hashtag": "#TRMTicari #Dayanışma #UmudunIşığı"
            },
            "facebook": {
                "max_karakter": 5000,
                "hashtag": "#TRMTicari #Dayanışma #UmudunIşığı #ToplumsalEtki"
            },
            "instagram": {
                "max_karakter": 2200,
                "hashtag": "#TRMTicari #Dayanışma #UmudunIşığı #İlhamVericiHikayeler"
            },
            "linkedin": {
                "max_karakter": 3000,
                "hashtag": "#TRMTicari #Dayanışma #ToplumsalSorumluluk #SosyalEtki"
            }
        }
        
        self.log_dosyasi = os.path.join("logs", f"storyteller_{agent_id}.log")
        self.setup_logging()
        self.log(f"📖 {self.name} başlatılıyor...", "INFO")
        self.log(f"📚 Hikaye veritabanı yüklendi: {len(self.hikaye_veritabani)} hikaye", "INFO")
        self.log(f"💬 Merhamet dili şablonları yüklendi: {len(self.merhamet_dili_sablonlari)} şablon", "INFO")
    
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
    
    def hikaye_sec(self) -> Dict[str, Any]:
        """
        Hikaye veritabanından rastgele bir hikaye seçer.
        
        Returns:
            Dict: Seçilen hikaye
        """
        import random
        hikaye = random.choice(self.hikaye_veritabani)
        self.log(f"📖 Hikaye seçildi: {hikaye['kisi_adi']}", "INFO")
        return hikaye
    
    def hikaye_duzenle(self, hikaye: Dict[str, Any], platform: str = "facebook") -> str:
        """
        Hikayeyi merhamet dili ile düzenler.
        
        Args:
            hikaye: Hikaye bilgileri
            platform: Platform adı
            
        Returns:
            str: Düzenlenmiş hikaye metni
        """
        format_info = self.platform_formatlari.get(platform, self.platform_formatlari["facebook"])
        
        baslik = self.merhamet_dili_sablonlari["baslik"].format(
            kisi_adi=hikaye["kisi_adi"]
        )
        
        giris = self.merhamet_dili_sablonlari["giris"].format(
            kisi_adi=hikaye["kisi_adi"],
            durum=hikaye["durum"]
        )
        
        govde = self.merhamet_dili_sablonlari["govde"].format(
            kisi_adi=hikaye["kisi_adi"],
            onceki_durum=hikaye["onceki_durum"],
            simdiki_durum=hikaye["simdiki_durum"],
            hikaye=hikaye["hikaye"]
        )
        
        kapanis = self.merhamet_dili_sablonlari["kapanis"]
        
        tam_metin = f"{baslik}\n\n{giris}\n\n{govde}\n\n{kapanis}\n\n{format_info['hashtag']}"
        
        # Karakter limiti kontrolü
        if len(tam_metin) > format_info["max_karakter"]:
            tam_metin = tam_metin[:format_info["max_karakter"] - 3] + "..."
        
        self.log(f"✍️ Hikaye düzenlendi: {platform} ({len(tam_metin)} karakter)", "INFO")
        return tam_metin
    
    def hikaye_yayinla(self, hikaye_metni: str, platform: str) -> Dict[str, Any]:
        """
        Hikayeyi belirtilen platformda yayınlar.
        
        Args:
            hikaye_metni: Hikaye metni
            platform: Platform adı
            
        Returns:
            Dict: Yayın sonucu
        """
        # Simülasyon - Gerçek API entegrasyonu gerektirir
        sonuc = {
            "platform": platform,
            "yayin_durumu": "basarili",
            "yayin_zamani": datetime.now().isoformat(),
            "karakter_sayisi": len(hikaye_metni),
            "etkilesim": {
                "goruntulenme": 0,
                "begeni": 0,
                "yorum": 0,
                "paylasim": 0
            }
        }
        
        self.log(f"📢 Hikaye yayınlandı: {platform}", "INFO")
        return sonuc
    
    def hikaye_raporu_olustur(self, yayinlar: List[Dict[str, Any]]) -> str:
        """
        Hikaye yayınlarını raporlar.
        
        Args:
            yayinlar: Yayın listesi
            
        Returns:
            str: Rapor dosyası yolu
        """
        rapor_dosyasi = os.path.join("reports", f"storyteller_rapor_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        os.makedirs("reports", exist_ok=True)
        
        rapor = {
            "rapor_tarihi": datetime.now().isoformat(),
            "ajan_id": self.agent_id,
            "ajan_adi": self.name,
            "toplam_yayin": len(yayinlar),
            "platformlar": list(set([y["platform"] for y in yayinlar])),
            "yayinlar": yayinlar,
            "ozet": {
                "toplam_karakter": sum([y["karakter_sayisi"] for y in yayinlar]),
                "ortalama_karakter": sum([y["karakter_sayisi"] for y in yayinlar]) / len(yayinlar) if yayinlar else 0
            }
        }
        
        with open(rapor_dosyasi, "w", encoding="utf-8") as f:
            json.dump(rapor, f, indent=4, ensure_ascii=False)
        
        self.log(f"📊 Hikaye raporu oluşturuldu: {rapor_dosyasi}", "INFO")
        return rapor_dosyasi
    
    def run(self):
        """Ajanın ana çalışma döngüsü."""
        self.refresh_config()
        self.log(f"📖 {self.name} çalışmaya başladı", "INFO")
        
        try:
            yayinlar = []
            
            # Her platform için hikaye seç ve yayınla
            for platform in self.platform_formatlari.keys():
                # Hikaye seç
                hikaye = self.hikaye_sec()
                
                # Hikayeyi düzenle
                hikaye_metni = self.hikaye_duzenle(hikaye, platform)
                
                # Hikayeyi yayınla
                yayin_sonuc = self.hikaye_yayinla(hikaye_metni, platform)
                yayinlar.append(yayin_sonuc)
            
            # Raporla
            rapor_dosyasi = self.hikaye_raporu_olustur(yayinlar)
            self.log(f"✅ {len(yayinlar)} hikaye yayınlandı ve raporlandı", "INFO")
            
            # CPU ve API simülasyonu
            self.cpu_yuk = 18 + (len(yayinlar) * 4)
            self.api_gecikme = 85 + (len(yayinlar) * 9)
            
            self.log(f"⚡ CPU Yükü: {self.cpu_yuk}%, API Gecikme: {self.api_gecikme}ms", "INFO")
            
        except Exception as e:
            self.log(f"❌ Hata oluştu: {e}", "ERROR")
            self.cpu_yuk = 0
            self.api_gecikme = 0
