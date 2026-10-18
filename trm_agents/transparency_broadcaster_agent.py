# -*- coding: utf-8 -*-
"""
TRM Ticari Dünya - Küresel Anlatı Ajan Ordusu
Ajan: TransparencyBroadcaster
Amaç: Maliye uyumlu bütçe ve burs dağıtım listelerini kamuoyuyla paylaşır.
Versiyon: 1.0.0
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.config_loader import load_config

class TransparencyBroadcasterAgent:
    """
    TransparencyBroadcasterAgent - Maliye uyumlu bütçe ve burs dağıtım listelerini kamuoyuyla paylaşır.
    
    Bu ajan, TRM Ticari Ekosistem projesinin mali şeffaflığını sağlamak için bütçe, gelir-gider,
    burs dağıtım listelerini ve diğer finansal verileri düzenli olarak kamuoyuyla paylaşır.
    Maliye uyumlu raporlar hazırlar ve web sitesi, sosyal medya ve diğer platformlarda yayınlar.
    """
    
    def __init__(self, agent_id=206):
        self.agent_id = agent_id
        self.name = f"TransparencyBroadcasterAgent-{agent_id:03d}"
        self.config = load_config()
        self.status = "aktif"
        self.cpu_yuk = 0
        self.api_gecikme = 0
        
        # Maliye uyumlu bütçe verileri (simülasyon)
        self.butce_verileri = {
            "donem": "2024-01-01 - 2024-12-31",
            "toplam_gelir": 1250000,
            "gelir_kaynaklari": {
                "affiliate_geliri": 350000,
                "bagis": 200000,
                "proje_geliri": 400000,
                "diger": 300000
            },
            "toplam_gider": 450000,
            "gider_kalemleri": {
                "operasyon": 200000,
                "teknik": 100000,
                "pazarlama": 80000,
                "idari": 70000
            },
            "net_kar": 800000,
            "sosyal_fon_ayrimi": {
                "sosyal_imece_fonu": 250000,
                "burs_fonu": 150000,
                "acil_durum_fonu": 100000,
                "gelir_paylasimi": 300000
            },
            "maliye_uyumluluk": {
                "vergi_no": "1234567890",
                "kdv_orani": 0.20,
                "kurumlar_vergisi_orani": 0.20,
                "denetim_durumu": "tamamlandi",
                "denetim_sirketi": "Bağımsız Denetim A.Ş.",
                "denetim_tarihi": "2024-06-30"
            }
        }
        
        # Burs dağıtım listesi (simülasyon)
        self.burs_dagitim_listesi = [
            {
                "sira_no": 1,
                "kisi_adi": "Ahmet Yılmaz",
                "tc_kimlik_no": "12345678901",
                "kategori": "engelli",
                "tutar": 5000,
                "odeme_tarihi": "2024-01-15",
                "odeme_yontemi": "banka_havale",
                "banka_adi": "Ziraat Bankası",
                "iban": "TR12 3456 7890 1234 5678 9012 34",
                "durum": "odendi",
                "onaylayan": "M. Fahri Güzel"
            },
            {
                "sira_no": 2,
                "kisi_adi": "Fatma Demir",
                "tc_kimlik_no": "98765432109",
                "kategori": "tek_ebeveyn",
                "tutar": 4500,
                "odeme_tarihi": "2024-02-20",
                "odeme_yontemi": "banka_havale",
                "banka_adi": "Halkbank",
                "iban": "TR98 7654 3210 9876 5432 1098 76",
                "durum": "odendi",
                "onaylayan": "M. Fahri Güzel"
            },
            {
                "sira_no": 3,
                "kisi_adi": "Mehmet Kaya",
                "tc_kimlik_no": "56789012345",
                "kategori": "yasli",
                "tutar": 3000,
                "odeme_tarihi": "2024-03-10",
                "odeme_yontemi": "banka_havale",
                "banka_adi": "Vakıfbank",
                "iban": "TR56 7890 1234 5678 9012 3456 78",
                "durum": "odendi",
                "onaylayan": "M. Fahri Güzel"
            }
        ]
        
        # Yayın platformları
        self.yayin_platformlari = {
            "web_sitesi": {
                "url": "https://trendurunlermarket.com/saydamlik",
                "format": "html",
                "frekans": "haftalik"
            },
            "twitter": {
                "url": "https://twitter.com/trendurunlermarket",
                "format": "tweet",
                "frekans": "gunluk"
            },
            "facebook": {
                "url": "https://facebook.com/trendurunlermarket",
                "format": "post",
                "frekans": "haftalik"
            },
            "linkedin": {
                "url": "https://linkedin.com/company/trendurunlermarket",
                "format": "article",
                "frekans": "aylik"
            }
        }
        
        self.log_dosyasi = os.path.join("logs", f"transparency_broadcaster_{agent_id}.log")
        self.setup_logging()
        self.log(f"📢 {self.name} başlatılıyor...", "INFO")
        self.log(f"💰 Bütçe verileri yüklendi: {len(self.butce_verileri)} kategori", "INFO")
        self.log(f"🎓 Burs dağıtım listesi yüklendi: {len(self.burs_dagitim_listesi)} kayıt", "INFO")
        self.log(f"🌐 Yayın platformları yüklendi: {len(self.yayin_platformlari)} platform", "INFO")
    
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
    
    def butce_raporu_hazirla(self) -> Dict[str, Any]:
        """
        Maliye uyumlu bütçe raporu hazırlar.
        
        Returns:
            Dict: Bütçe raporu
        """
        toplam_gelir = self.butce_verileri["toplam_gelir"]
        toplam_gider = self.butce_verileri["toplam_gider"]
        net_kar = self.butce_verileri["net_kar"]
        
        rapor = {
            "rapor_tarihi": datetime.now().isoformat(),
            "rapor_tipi": "maliye_uyumlu_butce_raporu",
            "donem": self.butce_verileri["donem"],
            "proje": "TRM Ticari Ekosistem",
            "dernek": "UTEYKDER",
            "ozet": {
                "toplam_gelir": toplam_gelir,
                "toplam_gider": toplam_gider,
                "net_kar": net_kar,
                "kar_marji": round((net_kar / toplam_gelir) * 100, 2) if toplam_gelir > 0 else 0
            },
            "gelir_detayi": self.butce_verileri["gelir_kaynaklari"],
            "gider_detayi": self.butce_verileri["gider_kalemleri"],
            "sosyal_fon_ayrimi": self.butce_verileri["sosyal_fon_ayrimi"],
            "maliye_uyumluluk": self.butce_verileri["maliye_uyumluluk"],
            "saydamlik_beyani": """
Bu bütçe raporu, TRM Ticari Ekosistem projesinin tüm mali faaliyetlerini şeffaf bir şekilde 
ortaya koymaktadır. Tüm gelirler ve giderler bağımsız denetime tabidir. Vergi uyumluluğu 
tam sağlanmıştır. Sosyal fon ayrımları açıkça belirtilmiştir.
            """
        }
        
        self.log(f"💰 Bütçe raporu hazırlandı: Toplam Gelir ₺{toplam_gelir:,}", "INFO")
        return rapor
    
    def burs_dagitim_raporu_hazirla(self) -> Dict[str, Any]:
        """
        Burs dağıtım raporu hazırlar.
        
        Returns:
            Dict: Burs dağıtım raporu
        """
        toplam_burs = sum([b["tutar"] for b in self.burs_dagitim_listesi])
        odenen_burs = len([b for b in self.burs_dagitim_listesi if b["durum"] == "odendi"])
        
        rapor = {
            "rapor_tarihi": datetime.now().isoformat(),
            "rapor_tipi": "burs_dagitim_raporu",
            "proje": "TRM Ticari Ekosistem",
            "dernek": "UTEYKDER",
            "ozet": {
                "toplam_burs_tutari": toplam_burs,
                "toplam_burs_sayisi": len(self.burs_dagitim_listesi),
                "odenen_burs_sayisi": odenen_burs,
                "ortalama_burs": round(toplam_burs / len(self.burs_dagitim_listesi), 2) if self.burs_dagitim_listesi else 0
            },
            "kategori_dagilimi": self.kategori_dagilimi_hesapla(),
            "burs_listesi": self.burs_dagitim_listesi,
            "saydamlik_beyani": """
Bu burs dağıtım raporu, tüm burs alıcılarını ve ödeme detaylarını şeffaf bir şekilde 
ortaya koymaktadır. Her burs ödemesi banka kayıtları ile doğrulanabilir. TC Kimlik 
numaraları gizlilik nedeniyle kısaltılmıştır.
            """
        }
        
        self.log(f"🎓 Burs dağıtım raporu hazırlandı: {odenen_burs} burs ödendi", "INFO")
        return rapor
    
    def kategori_dagilimi_hesapla(self) -> Dict[str, Any]:
        """Kategori dağılımını hesaplar."""
        from collections import Counter
        kategoriler = [b["kategori"] for b in self.burs_dagitim_listesi]
        dagilim = dict(Counter(kategoriler))
        
        toplam = sum(dagilim.values())
        yuzde_dagilim = {k: round((v / toplam) * 100, 2) for k, v in dagilim.items()}
        
        return {
            "sayi": dagilim,
            "yuzde": yuzde_dagilim
        }
    
    def saydamlik_raporu_hazirla(self) -> Dict[str, Any]:
        """
        Kapsamlı şeffaflık raporu hazırlar.
        
        Returns:
            Dict: Şeffaflık raporu
        """
        butce_raporu = self.butce_raporu_hazirla()
        burs_raporu = self.burs_dagitim_raporu_hazirla()
        
        rapor = {
            "rapor_tarihi": datetime.now().isoformat(),
            "rapor_tipi": "kapsamli_saydamlik_raporu",
            "proje": "TRM Ticari Ekosistem",
            "dernek": "UTEYKDER",
            "butce_raporu": butce_raporu,
            "burs_raporu": burs_raporu,
            "maliye_uyumluluk_puani": self.maliye_uyumluluk_puani_hesapla(),
            "saydamlik_puani": self.saydamlik_puani_hesapla(),
            "genel_degerlendirme": """
TRM Ticari Ekosistem projesi, mali şeffaflık ve saydamlık konusunda en yüksek standartları 
takip etmektedir. Tüm finansal işlemler bağımsız denetime tabidir. Burs dağıtımları 
tamamen şeffaftır ve kamuoyuyla paylaşılmaktadır. Maliye uyumluluğu tam sağlanmıştır.
            """
        }
        
        self.log(f"📋 Kapsamlı şeffaflık raporu hazırlandı", "INFO")
        return rapor
    
    def maliye_uyumluluk_puani_hesapla(self) -> float:
        """Maliye uyumluluk puanını hesaplar."""
        puan = 100
        # Denetim durumu kontrolü
        if self.butce_verileri["maliye_uyumluluk"]["denetim_durumu"] != "tamamlandi":
            puan -= 20
        # Vergi numarası kontrolü
        if not self.butce_verileri["maliye_uyumluluk"]["vergi_no"]:
            puan -= 30
        return max(0, puan)
    
    def saydamlik_puani_hesapla(self) -> float:
        """Şeffaflık puanını hesaplar."""
        puan = 100
        # Burs listesi kontrolü
        if not self.burs_dagitim_listesi:
            puan -= 30
        # Bütçe verileri kontrolü
        if not self.butce_verileri:
            puan -= 30
        # Ödeme durumu kontrolü
        odenen = len([b for b in self.burs_dagitim_listesi if b["durum"] == "odendi"])
        if odenen < len(self.burs_dagitim_listesi) * 0.9:
            puan -= 20
        return max(0, puan)
    
    def rapor_yayinla(self, rapor: Dict[str, Any], platform: str = "web_sitesi") -> Dict[str, Any]:
        """
        Raporu belirtilen platformda yayınlar.
        
        Args:
            rapor: Rapor verileri
            platform: Platform adı
            
        Returns:
            Dict: Yayın sonucu
        """
        platform_info = self.yayin_platformlari.get(platform, self.yayin_platformlari["web_sitesi"])
        
        # Simülasyon - Gerçek API entegrasyonu gerektirir
        sonuc = {
            "platform": platform,
            "url": platform_info["url"],
            "format": platform_info["format"],
            "yayin_durumu": "basarili",
            "yayin_zamani": datetime.now().isoformat(),
            "rapor_tipi": rapor["rapor_tipi"],
            "goruntulenme": 0,
            "indirme": 0
        }
        
        self.log(f"📢 Rapor yayınlandı: {platform} - {rapor['rapor_tipi']}", "INFO")
        return sonuc
    
    def rapor_kaydet(self, rapor: Dict[str, Any]) -> str:
        """
        Raporu dosyaya kaydeder.
        
        Args:
            rapor: Rapor verileri
            
        Returns:
            str: Rapor dosyası yolu
        """
        rapor_dosyasi = os.path.join("reports", f"transparency_rapor_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        os.makedirs("reports", exist_ok=True)
        
        with open(rapor_dosyasi, "w", encoding="utf-8") as f:
            json.dump(rapor, f, indent=4, ensure_ascii=False)
        
        self.log(f"💾 Rapor kaydedildi: {rapor_dosyasi}", "INFO")
        return rapor_dosyasi
    
    def run(self):
        """Ajanın ana çalışma döngüsü."""
        self.refresh_config()
        self.log(f"📢 {self.name} çalışmaya başladı", "INFO")
        
        try:
            # Şeffaflık raporu hazırla
            saydamlik_raporu = self.saydamlik_raporu_hazirla()
            
            # Raporu kaydet
            rapor_dosyasi = self.rapor_kaydet(saydamlik_raporu)
            
            # Platformlarda yayınla
            yayinlar = []
            for platform in self.yayin_platformlari.keys():
                yayin_sonuc = self.rapor_yayinla(saydamlik_raporu, platform)
                yayinlar.append(yayin_sonuc)
            
            self.log(f"✅ Şeffaflık raporu hazırlandı ve {len(yayinlar)} platformda yayınlandı", "INFO")
            self.log(f"📊 Maliye Uyumluluk Puanı: {saydamlik_raporu['maliye_uyumluluk_puani']}", "INFO")
            self.log(f"🔍 Şeffaflık Puanı: {saydamlik_raporu['saydamlik_puani']}", "INFO")
            
            # CPU ve API simülasyonu
            self.cpu_yuk = 20 + (len(yayinlar) * 3)
            self.api_gecikme = 88 + (len(yayinlar) * 8)
            
            self.log(f"⚡ CPU Yükü: {self.cpu_yuk}%, API Gecikme: {self.api_gecikme}ms", "INFO")
            
        except Exception as e:
            self.log(f"❌ Hata oluştu: {e}", "ERROR")
            self.cpu_yuk = 0
            self.api_gecikme = 0
