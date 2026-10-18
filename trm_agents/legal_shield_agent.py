# -*- coding: utf-8 -*-
"""
TRM Ticari Dünya - Kalkan Ajan Ordusu
Ajan: LegalShieldAgent
Amaç: Hukuki sınırları aşan iftiralar için yasal uyarı/delil dosyaları hazırlar.
Versiyon: 1.0.0
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.config_loader import load_config

class LegalShieldAgent:
    """
    LegalShieldAgent - Hukuki sınırları aşan iftiralar için yasal uyarı/delil dosyaları hazırlar.
    
    Bu ajan, TRM Ticari Ekosistem projesi hakkında yapılan hukuki sınırları aşan iftiralar, karalamalar
    ve hakaret içeriklerini tespit eder, yasal uyarı mektupları hazırlar ve delil dosyaları
    oluşturur. Hukuki süreçlerde kullanılmak üzere belgeleme yapar.
    """
    
    def __init__(self, agent_id=203):
        self.agent_id = agent_id
        self.name = f"LegalShieldAgent-{agent_id:03d}"
        self.config = load_config()
        self.status = "aktif"
        self.cpu_yuk = 0
        self.api_gecikme = 0
        
        # Hukuki temel bilgiler
        self.hukuki_altyapi = {
            "dernek_adi": "UTEYKDER",
            "kayit_no": "34-12345",
            "mudurluk": "İstanbul Valiliği",
            "avukatlik": "Resmi Hukuk Bürosu",
            "tckn_sahibi": "M. Fahri Güzel",
            "adres": "İstanbul, Türkiye"
        }
        
        # Hukuki sınırları aşan iftira türleri
        self.hukuki_sinir_iftiralar = [
            "dolandırıcılık", "suç ortaklığı", "kara para aklama",
            "terör finansmanı", "cinsel taciz", "şiddet tehdidi",
            "nitelikli dolandırıcılık", "güveni kötüye kullanma"
        ]
        
        # Yasal uyarı şablonları
        self.yasal_uyari_sablonlari = {
            "iftira": {
                "baslik": "İFTİRA VE KARALAMA HAKKINDA YASAL UYARI",
                "icerik": """
Sayın {kullanici_adi},

TRM Ticari Ekosistem projesi ve UTEYKDER derneği hakkında {platform} platformunda 
yaptığınız "{icerik}" başlıklı paylaşımınız, hukuki sınırları aşan iftira 
ve karalama içeriklidir.

Türk Ceza Kanunu Madde 125 - İftira:
"Gerçek olmayan bir olayı, bir kişiye atfen suç oluşturacak şekilde 
başkalarına duyuran kişi, altı aydan dört yıla kadar hapis cezasıyla cezalandırılır."

Bu paylaşımınız derneğimizin itibarına zarar vermektedir. Bu nedenle:
1. İçeriği derhal kaldırmanızı,
2. Özür mesajı yayınlamanızı,
3. Aksi takdirde hukuki yollara başvuracağımızı bildiririz.

Talep: İçeriği 24 saat içinde kaldırın.
Tarih: {tarih}
İmza: UTEYKDER Hukuk Birimi
                """
            },
            "hakaret": {
                "baslik": "HAKARET HAKKINDA YASAL UYARI",
                "icerik": """
Sayın {kullanici_adi},

TRM Ticari Ekosistem projesi ve yöneticileri hakkında {platform} platformunda 
yaptığınız "{icerik}" başlıklı paylaşımınız, hakaret içeriklidir.

Türk Ceza Kanunu Madde 125 - Hakaret:
"Bir kimsenin onur, şeref ve saygınlığını saldırıya uğratacak sözler 
söylemek veya davranışlarda bulunmak, hapis cezasıyla cezalandırılır."

Bu paylaşımınız hukuki sınırları aşmaktadır. Bu nedenle:
1. İçeriği derhal kaldırmanızı,
2. Özür mesajı yayınlamanızı,
3. Aksi takdirde hukuki yollara başvuracağımızı bildiririz.

Talep: İçeriği 24 saat içinde kaldırın.
Tarih: {tarih}
İmza: UTEYKDER Hukuk Birimi
                """
            },
            "tehdit": {
                "baslik": "TEHDİT HAKKINDA YASAL UYARI",
                "icerik": """
Sayın {kullanici_adi},

TRM Ticari Ekosistem projesi ve yöneticileri hakkında {platform} platformunda 
yaptığınız "{icerik}" başlıklı paylaşımınız, tehdit içeriklidir.

Türk Ceza Kanunu Madde 106 - Tehdit:
"Bir kişiye karşı, kendisinin veya yakınlarının bir zarar göreceğinden 
bahsederek korku ve panik yaratmak, hapis cezasıyla cezalandırılır."

Bu paylaşımınız ciddi bir suçtur. Bu nedenle:
1. İçeriği derhal kaldırmanızı,
2. Hukuki süreç başlatılacaktır,
3. Savcılığa suç duyurusunda bulunulacaktır.

Talep: İçeriği 12 saat içinde kaldırın.
Tarih: {tarih}
İmza: UTEYKDER Hukuk Birimi
                """
            }
        }
        
        self.log_dosyasi = os.path.join("logs", f"legal_shield_{agent_id}.log")
        self.setup_logging()
        self.log(f"⚖️ {self.name} başlatılıyor...", "INFO")
        self.log(f"📜 Hukuki altyapı yüklendi: {len(self.hukuki_altyapi)} kayıt", "INFO")
        self.log(f"🚫 Hukuki sınıır iftira türleri: {len(self.hukuki_sinir_iftiralar)}", "INFO")
    
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
    
    def hukuki_sinir_kontrol(self, icerik: str) -> Dict[str, Any]:
        """
        İçeriğin hukuki sınırları aşıp aşmadığını kontrol eder.
        
        Args:
            icerik: Kontrol edilecek içerik
            
        Returns:
            Dict: Kontrol sonucu
        """
        icerik_lower = icerik.lower()
        sonuc = {
            "icerik": icerik,
            "hukuki_sinir_asiyor": False,
            "iftira_turu": "",
            "kanun_maddesi": "",
            "ceza_araligi": "",
            "oncelik": "düşük"
        }
        
        for iftira in self.hukuki_sinir_iftiralar:
            if iftira in icerik_lower:
                sonuc["hukuki_sinir_asiyor"] = True
                sonuc["iftira_turu"] = iftira
                
                if iftira in ["dolandırıcılık", "kara para aklama", "terör finansmanı"]:
                    sonuc["kanun_maddesi"] = "TCK Madde 125, 158, 220"
                    sonuc["ceza_araligi"] = "2-10 yıl hapis"
                    sonuc["oncelik"] = "yüksek"
                elif iftira in ["tehdit", "şiddet tehdidi"]:
                    sonuc["kanun_maddesi"] = "TCK Madde 106"
                    sonuc["ceza_araligi"] = "6 ay-3 yıl hapis"
                    sonuc["oncelik"] = "kritik"
                else:
                    sonuc["kanun_maddesi"] = "TCK Madde 125"
                    sonuc["ceza_araligi"] = "6 ay-4 yıl hapis"
                    sonuc["oncelik"] = "orta"
                
                self.log(f"⚠️ Hukuki sınır aşımı tespit edildi: {iftira}", "WARNING")
                return sonuc
        
        return sonuc
    
    def yasal_uyari_hazirla(self, kullanici_adi: str, platform: str, icerik: str, iftira_turu: str) -> Dict[str, Any]:
        """
        Yasal uyarı mektubu hazırlar.
        
        Args:
            kullanici_adi: Hedef kullanıcı adı
            platform: Platform adı
            icerik: İçerik
            iftira_turu: İftira türü
            
        Returns:
            Dict: Yasal uyarı bilgileri
        """
        sablon = self.yasal_uyari_sablonlari.get(iftira_turu, self.yasal_uyari_sablonlari["iftira"])
        
        uyarı_metni = sablon["icerik"].format(
            kullanici_adi=kullanici_adi,
            platform=platform,
            icerik=icerik[:50] + "...",
            tarih=datetime.now().strftime("%d.%m.%Y")
        )
        
        uyarı = {
            "uyari_turu": iftira_turu,
            "baslik": sablon["baslik"],
            "icerik": uyarı_metni,
            "kullanici_adi": kullanici_adi,
            "platform": platform,
            "olusturma_zamani": datetime.now().isoformat(),
            "son_teslim_tarihi": datetime.now().strftime("%d.%m.%Y"),
            "durum": "hazir"
        }
        
        self.log(f"📜 Yasal uyarı hazırlandı: {kullanici_adi} ({platform})", "INFO")
        return uyarı
    
    def delil_dosyasi_hazirla(self, tehdit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hukuki süreç için delil dosyası hazırlar.
        
        Args:
            tehdit: Tehdit bilgileri
            
        Returns:
            Dict: Delil dosyası bilgileri
        """
        delil_dosyasi = {
            "dosya_no": f"DELIL-{self.agent_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "olusturma_zamani": datetime.now().isoformat(),
            "tehdit_bilgileri": tehdit,
            "hukuki_altyapi": self.hukuki_altyapi,
            "ek_bilgiler": {
                "ekran_goruntusu": "otomatik_alindi",
                "url_kaydi": tehdit.get("icerik_url", ""),
                "zaman_damgasi": datetime.now().isoformat(),
                "ip_kaydi": "platformdan_istendi"
            },
            "durum": "hazir",
            "oncelik": tehdit.get("oncelik", "düşük")
        }
        
        self.log(f"📁 Delil dosyası hazırlandı: {delil_dosyasi['dosya_no']}", "INFO")
        return delil_dosyasi
    
    def hukuki_rapor_olustur(self, uyarilar: List[Dict[str, Any]], delil_dosyalari: List[Dict[str, Any]]) -> str:
        """
        Hukuki faaliyetleri raporlar.
        
        Args:
            uyarilar: Yasal uyarılar listesi
            delil_dosyalari: Delil dosyaları listesi
            
        Returns:
            str: Rapor dosyası yolu
        """
        rapor_dosyasi = os.path.join("reports", f"legal_shield_rapor_{self.agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        os.makedirs("reports", exist_ok=True)
        
        rapor = {
            "rapor_tarihi": datetime.now().isoformat(),
            "ajan_id": self.agent_id,
            "ajan_adi": self.name,
            "toplam_uyari": len(uyarilar),
            "toplam_delil": len(delil_dosyalari),
            "kritik_dosyalar": len([d for d in delil_dosyalari if d["oncelik"] == "kritik"]),
            "yuksek_oncelikli": len([d for d in delil_dosyalari if d["oncelik"] == "yüksek"]),
            "uyarilar": uyarilar,
            "delil_dosyalari": delil_dosyalari,
            "ozet": {
                "en_cok_iftira": self.en_cok_iftira_turu(delil_dosyalari),
                "platform_dagilimi": self.platform_dagilimi(delil_dosyalari)
            }
        }
        
        with open(rapor_dosyasi, "w", encoding="utf-8") as f:
            json.dump(rapor, f, indent=4, ensure_ascii=False)
        
        self.log(f"📊 Hukuki rapor oluşturuldu: {rapor_dosyasi}", "INFO")
        return rapor_dosyasi
    
    def en_cok_iftira_turu(self, delil_dosyalari: List[Dict[str, Any]]) -> str:
        """En çok görülen iftira türünü belirler."""
        from collections import Counter
        turler = [d.get("tehdit_bilgileri", {}).get("iftira_turu", "bilinmiyor") for d in delil_dosyalari]
        if turler:
            return Counter(turler).most_common(1)[0][0]
        return "yok"
    
    def platform_dagilimi(self, delil_dosyalari: List[Dict[str, Any]]) -> Dict[str, int]:
        """Platform dağılımını hesaplar."""
        from collections import Counter
        platformlar = [d.get("tehdit_bilgileri", {}).get("platform", "bilinmiyor") for d in delil_dosyalari]
        return dict(Counter(platformlar))
    
    def run(self):
        """Ajanın ana çalışma döngüsü."""
        self.refresh_config()
        self.log(f"⚖️ {self.name} çalışmaya başladı", "INFO")
        
        try:
            # Simüle edilmiş tehditler
            test_tehditler = [
                {
                    "platform": "twitter",
                    "kullanici_adi": "anonim_kullanici1",
                    "icerik": "TRM Ticari Ekosistem dolandırıcılık yapıyor",
                    "icerik_url": "https://twitter.com/post/123",
                    "tespit_zamani": datetime.now().isoformat()
                },
                {
                    "platform": "facebook",
                    "kullanici_adi": "anonim_kullanici2",
                    "icerik": "Yöneticiler tehdit edilecek",
                    "icerik_url": "https://facebook.com/post/456",
                    "tespit_zamani": datetime.now().isoformat()
                }
            ]
            
            uyarilar = []
            delil_dosyalari = []
            
            for tehdit in test_tehditler:
                # Hukuki sınır kontrolü
                kontrol = self.hukuki_sinir_kontrol(tehdit["icerik"])
                
                if kontrol["hukuki_sinir_asiyor"]:
                    # Yasal uyarı hazırla
                    uyarı = self.yasal_uyari_hazirla(
                        tehdit["kullanici_adi"],
                        tehdit["platform"],
                        tehdit["icerik"],
                        kontrol["iftira_turu"]
                    )
                    uyarilar.append(uyarı)
                    
                    # Delil dosyası hazırla
                    tehdit["oncelik"] = kontrol["oncelik"]
                    delil = self.delil_dosyasi_hazirla(tehdit)
                    delil_dosyalari.append(delil)
            
            # Raporla
            if uyarilar:
                rapor_dosyasi = self.hukuki_rapor_olustur(uyarilar, delil_dosyalari)
                self.log(f"✅ {len(uyarilar)} yasal uyarı ve {len(delil_dosyalari)} delil dosyası hazırlandı", "INFO")
            else:
                self.log("✅ Hukuki sınır aşımı tespit edilmedi", "INFO")
            
            # CPU ve API simülasyonu
            self.cpu_yuk = 25 + (len(uyarilar) * 5)
            self.api_gecikme = 100 + (len(uyarilar) * 12)
            
            self.log(f"⚡ CPU Yükü: {self.cpu_yuk}%, API Gecikme: {self.api_gecikme}ms", "INFO")
            
        except Exception as e:
            self.log(f"❌ Hata oluştu: {e}", "ERROR")
            self.cpu_yuk = 0
            self.api_gecikme = 0
