# -*- coding: utf-8 -*-
"""
TRM Ticari Dünya - Küresel Anlatı Ajan Ordusu
Ajan: PublicBenefitAnalystAgent
Amaç: Projenin ekonomik ve toplumsal katkılarını şeffaf şekilde raporlar.
Versiyon: 1.0.0
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.config_loader import load_config

class PublicBenefitAnalystAgent:
    """
    PublicBenefitAnalystAgent - Projenin ekonomik ve toplumsal katkılarını şeffaf şekilde raporlar.
    
    Bu ajan, TRM Ticari Ekosistem projesinin ekonomik ve toplumsal etkilerini analiz eder, 
    şeffaf raporlar hazırlar ve kamuoyuyla paylaşır. Gelir dağılımı, burs 
    dağıtımı, sosyal güvenlik ve toplumsal fayda gibi metrikleri izler.
    """
    
    def __init__(self, agent_id=205):
        self.agent_id = agent_id
        self.name = f"PublicBenefitAnalystAgent-{agent_id:03d}"
        self.config = load_config()
        self.status = "aktif"
        self.cpu_yuk = 0
        self.api_gecikme = 0
        
        # Ekonomik metrikler (simülasyon)
        self.ekonomik_metrikler = {
            "toplam_gelir": 1250000,
            "toplam_gider": 450000,
            "net_kar": 800000,
            "affiliate_geliri": 350000,
            "sosyal_imece_fonu": 250000,
            "burs_fonu": 150000,
            "operasyon_maliyeti": 200000
        }
        
        # Toplumsal metrikler (simülasyon)
        self.toplumsal_metrikler = {
            "faydalanan_kisi_sayisi": 1250,
            "engelli_destek": 350,
            "tek_ebeveyn_destek": 280,
            "yasli_destek": 420,
            "ogrenci_bursu": 200,
            "is_bulma_orani": 0.65,
            "gelir_artisi_orani": 0.45
        }
        
        # Burs dağıtım verileri (simülasyon)
        self.burs_dagitimi = [
            {
                "kisi_adi": "Ahmet Yılmaz",
                "kategori": "engelli",
                "tutar": 5000,
                "tarih": "2024-01-15",
                "durum": "odendi"
            },
            {
                "kisi_adi": "Fatma Demir",
                "kategori": "tek_ebeveyn",
                "tutar": 4500,
                "tarih": "2024-02-20",
                "durum": "odendi"
            },
            {
                "kisi_adi": "Mehmet Kaya",
                "kategori": "yasli",
                "tutar": 3000,
                "tarih": "2024-03-10",
                "durum": "odendi"
            }
        ]
        
        self.log_dosyasi = os.path.join("logs", f"public_benefit_analyst_{agent_id}.log")
        self.setup_logging()
        self.log(f"📊 {self.name} başlatılıyor...", "INFO")
        self.log(f"💰 Ekonomik metrikler yüklendi: {len(self.ekonomik_metrikler)} metrik", "INFO")
        self.log(f"👥 Toplumsal metrikler yüklendi: {len(self.toplumsal_metrikler)} metrik", "INFO")
        self.log(f"🎓 Burs dağıtım verileri yüklendi: {len(self.burs_dagitimi)} kayıt", "INFO")
    
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
    
    def ekonomik_analiz_yap(self) -> Dict[str, Any]:
        """
        Ekonomik analiz yapar.
        
        Returns:
            Dict: Ekonomik analiz sonucu
        """
        toplam_gelir = self.ekonomik_metrikler["toplam_gelir"]
        toplam_gider = self.ekonomik_metrikler["toplam_gider"]
        net_kar = self.ekonomik_metrikler["net_kar"]
        
        kar_marji = (net_kar / toplam_gelir) * 100 if toplam_gelir > 0 else 0
        gider_orani = (toplam_gider / toplam_gelir) * 100 if toplam_gelir > 0 else 0
        
        analiz = {
            "analiz_tarihi": datetime.now().isoformat(),
            "toplam_gelir": toplam_gelir,
            "toplam_gider": toplam_gider,
            "net_kar": net_kar,
            "kar_marji": round(kar_marji, 2),
            "gider_orani": round(gider_orani, 2),
            "affiliate_geliri": self.ekonomik_metrikler["affiliate_geliri"],
            "sosyal_imece_fonu": self.ekonomik_metrikler["sosyal_imece_fonu"],
            "burs_fonu": self.ekonomik_metrikler["burs_fonu"],
            "operasyon_maliyeti": self.ekonomik_metrikler["operasyon_maliyeti"],
            "gelir_kaynaklari": {
                "affiliate": round((self.ekonomik_metrikler["affiliate_geliri"] / toplam_gelir) * 100, 2),
                "diger": round(((toplam_gelir - self.ekonomik_metrikler["affiliate_geliri"]) / toplam_gelir) * 100, 2)
            }
        }
        
        self.log(f"💰 Ekonomik analiz tamamlandı: Kar Marjı %{analiz['kar_marji']}", "INFO")
        return analiz
    
    def toplumsal_analiz_yap(self) -> Dict[str, Any]:
        """
        Toplumsal analiz yapar.
        
        Returns:
            Dict: Toplumsal analiz sonucu
        """
        faydalanan_kisi = self.toplumsal_metrikler["faydalanan_kisi_sayisi"]
        
        analiz = {
            "analiz_tarihi": datetime.now().isoformat(),
            "faydalanan_kisi_sayisi": faydalanan_kisi,
            "kategori_dagilimi": {
                "engelli": self.toplumsal_metrikler["engelli_destek"],
                "tek_ebeveyn": self.toplumsal_metrikler["tek_ebeveyn_destek"],
                "yasli": self.toplumsal_metrikler["yasli_destek"],
                "ogrenci": self.toplumsal_metrikler["ogrenci_bursu"]
            },
            "is_bulma_orani": round(self.toplumsal_metrikler["is_bulma_orani"] * 100, 2),
            "gelir_artisi_orani": round(self.toplumsal_metrikler["gelir_artisi_orani"] * 100, 2),
            "toplam_burs": sum([b["tutar"] for b in self.burs_dagitimi]),
            "odenen_burs_sayisi": len([b for b in self.burs_dagitimi if b["durum"] == "odendi"])
        }
        
        self.log(f"👥 Toplumsal analiz tamamlandı: {faydalanan_kisi} kişi faydalandı", "INFO")
        return analiz
    
    def etki_analizi_yap(self) -> Dict[str, Any]:
        """
        Projenin toplumsal etkisini analiz eder.
        
        Returns:
            Dict: Etki analizi sonucu
        """
        ekonomik_analiz = self.ekonomik_analiz_yap()
        toplumsal_analiz = self.toplumsal_analiz_yap()
        
        etki_analizi = {
            "analiz_tarihi": datetime.now().isoformat(),
            "ekonomik_etki": {
                "yaratilan_gelir": ekonomik_analiz["toplam_gelir"],
                "dagitilan_gelir": ekonomik_analiz["net_kar"],
                "sosyal_fon": ekonomik_analiz["sosyal_imece_fonu"],
                "burs_fonu": ekonomik_analiz["burs_fonu"]
            },
            "toplumsal_etki": {
                "faydalanan_kisi": toplumsal_analiz["faydalanan_kisi_sayisi"],
                "is_bulma": round(toplumsal_analiz["faydalanan_kisi_sayisi"] * toplumsal_analiz["is_bulma_orani"] / 100),
                "gelir_artisi": round(toplumsal_analiz["faydalanan_kisi_sayisi"] * toplumsal_analiz["gelir_artisi_orani"] / 100)
            },
            "etki_skoru": self.etki_skoru_hesapla(ekonomik_analiz, toplumsal_analiz)
        }
        
        self.log(f"📈 Etki analizi tamamlandı: Etki Skoru {etki_analizi['etki_skoru']}", "INFO")
        return etki_analizi
    
    def etki_skoru_hesapla(self, ekonomik_analiz: Dict, toplumsal_analiz: Dict) -> float:
        """Etki skorunu hesaplar."""
        ekonomik_skor = (ekonomik_analiz["net_kar"] / 1000000) * 50  # Milyon TL başına 50 puan
        toplumsal_skor = (toplumsal_analiz["faydalanan_kisi_sayisi"] / 1000) * 50  # 1000 kişi başına 50 puan
        toplam_skor = min(100, ekonomik_skor + toplumsal_skor)
        return round(toplam_skor, 2)
    
    def kamuoyu_raporu_hazirla(self) -> Dict[str, Any]:
        """
        Kamuoyu için şeffaf rapor hazırlar.
        
        Returns:
            Dict: Kamuoyu raporu
        """
        etki_analizi = self.etki_analizi_yap()
        
        rapor = {
            "rapor_tarihi": datetime.now().isoformat(),
            "rapor_tipi": "kamuoyu_saydamlik_raporu",
            "proje_adi": "TRM Ticari Ekosistem",
            "dernek": "UTEYKDER",
            "ekonomik_ozet": {
                "toplam_gelir": etki_analizi["ekonomik_etki"]["yaratilan_gelir"],
                "dagitilan_gelir": etki_analizi["ekonomik_etki"]["dagitilan_gelir"],
                "sosyal_fon": etki_analizi["ekonomik_etki"]["sosyal_fon"],
                "burs_fonu": etki_analizi["ekonomik_etki"]["burs_fonu"]
            },
            "toplumsal_ozet": {
                "faydalanan_kisi": etki_analizi["toplumsal_etki"]["faydalanan_kisi"],
                "is_bulma": etki_analizi["toplumsal_etki"]["is_bulma"],
                "gelir_artisi": etki_analizi["toplumsal_etki"]["gelir_artisi"]
            },
            "etki_skoru": etki_analizi["etki_skoru"],
            "burs_dagitimi": self.burs_dagitimi,
            "saydamlik_beyani": """
Bu rapor, TRM Ticari Ekosistem projesinin tüm ekonomik ve toplumsal faaliyetlerini 
şeffaf bir şekilde ortaya koymaktadır. Tüm gelirler ve giderler bağımsız 
denetime tabidir. Burs dağıtımları tamamen şeffaftır ve kamuoyuyla paylaşılmaktadır.
            """
        }
        
        self.log(f"📋 Kamuoyu raporu hazırlandı", "INFO")
        return rapor
    
    def rapor_kaydet(self, rapor: Dict[str, Any]) -> str:
        """
        Raporu dosyaya kaydeder.
        
        Args:
            rapor: Rapor verileri
            
        Returns:
            str: Rapor dosyası yolu
        """
        rapor_dosyasi = os.path.join("reports", f"public_benefit_rapor_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        os.makedirs("reports", exist_ok=True)
        
        with open(rapor_dosyasi, "w", encoding="utf-8") as f:
            json.dump(rapor, f, indent=4, ensure_ascii=False)
        
        self.log(f"💾 Rapor kaydedildi: {rapor_dosyasi}", "INFO")
        return rapor_dosyasi
    
    def run(self):
        """Ajanın ana çalışma döngüsü."""
        self.refresh_config()
        self.log(f"📊 {self.name} çalışmaya başladı", "INFO")
        
        try:
            # Etki analizi yap
            etki_analizi = self.etki_analizi_yap()
            
            # Kamuoyu raporu hazırla
            kamuoyu_raporu = self.kamuoyu_raporu_hazirla()
            
            # Raporu kaydet
            rapor_dosyasi = self.rapor_kaydet(kamuoyu_raporu)
            
            self.log(f"✅ Etki analizi ve kamuoyu raporu tamamlandı", "INFO")
            self.log(f"📈 Etki Skoru: {etki_analizi['etki_skoru']}", "INFO")
            
            # CPU ve API simülasyonu
            self.cpu_yuk = 22
            self.api_gecikme = 95
            
            self.log(f"⚡ CPU Yükü: {self.cpu_yuk}%, API Gecikme: {self.api_gecikme}ms", "INFO")
            
        except Exception as e:
            self.log(f"❌ Hata oluştu: {e}", "ERROR")
            self.cpu_yuk = 0
            self.api_gecikme = 0
