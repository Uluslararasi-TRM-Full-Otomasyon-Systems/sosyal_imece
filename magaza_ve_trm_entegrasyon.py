import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class MagazaVeTRMEntegrasyonu:
    def __init__(self, config_dosyasi="entegrasyon_config.json"):
        self.config_dosyasi = config_dosyasi
        self.config = self.config_yukle()
        self.trm_sistem_aktif = True
        
    def config_yukle(self) -> Dict[str, Any]:
        """Entegrasyon konfigürasyonunu yükler"""
        varsayilan_config = {
            "magazalar": [],
            "trm_sistem_aktif": True,
            "urun_havuzu": [],
            "iban_havuzu": [],
            "api_entegrasyonlari": [],
            "trm_ana_iban": None,
            "sistem_bilgisi": {
                "versiyon": "1.0.0",
                "olusturma_tarihi": datetime.now().isoformat(),
                "max_urun_kapasitesi": 200000,
                "desteklenen_platformlar": ["trendurunlermarket.com", "hepsiburada.com", "n11.com", "amazon.com", "etsy.com"]
            }
        }
        
        if os.path.exists(self.config_dosyasi):
            with open(self.config_dosyasi, "r", encoding="utf-8") as f:
                yuklenen_config = json.load(f)
                # Eksik anahtarları varsayılan değerlerle tamamla
                for anahtar, deger in varsayilan_config.items():
                    if anahtar not in yuklenen_config:
                        yuklenen_config[anahtar] = deger
                return yuklenen_config
        return varsayilan_config
    
    def magaza_ekle(self, platform_adi: str, domain: str, api_anahtari: str, iban: str, 
                   urun_sayisi: int = 0, ulke: str = "TR") -> str:
        """
        Yerel veya yurtdışı e-ticaret firmalarını sisteme ekler.
        
        Args:
            platform_adi: Platform adı
            domain: Mağaza domain adresi
            api_anahtari: API entegrasyon anahtarı
            iban: Ödeme IBAN numarası
            urun_sayisi: Mağazadaki ürün sayısı (varsayılan: 0)
            ulke: Ülke kodu (varsayılan: TR)
            
        Returns:
            str: İşlem sonucu mesajı
        """
        yeni_magaza = {
            "platform": platform_adi,
            "domain": domain,
            "api_anahtari": api_anahtari,
            "iban": iban,
            "urun_sayisi": urun_sayisi,
            "ulke": ulke,
            "durum": "Entegre Edildi",
            "entegrasyon_tarihi": datetime.now().isoformat(),
            "son_guncelleme": datetime.now().isoformat(),
            "api_durumu": "Aktif",
            "odeme_sistemi": "Aktif"
        }
        
        self.config["magazalar"].append(yeni_magaza)
        self.kaydet()
        return f"{platform_adi} ({domain}) başarıyla TRM sistemine entegre edildi. {urun_sayisi} ürün aktif."
    
    def magaza_guncelle(self, domain: str, **kwargs) -> str:
        """
        Mevcut mağaza bilgilerini günceller.
        
        Args:
            domain: Mağaza domain adresi
            **kwargs: Güncellenecek alanlar
            
        Returns:
            str: İşlem sonucu mesajı
        """
        for magaza in self.config["magazalar"]:
            if magaza["domain"] == domain:
                magaza.update(kwargs)
                magaza["son_guncelleme"] = datetime.now().isoformat()
                self.kaydet()
                return f"{domain} mağazası başarıyla güncellendi."
        return f"{domain} mağazası bulunamadı."
    
    def magaza_sil(self, domain: str) -> str:
        """
        Mağazayı sistemden siler.
        
        Args:
            domain: Mağaza domain adresi
            
        Returns:
            str: İşlem sonucu mesajı
        """
        for i, magaza in enumerate(self.config["magazalar"]):
            if magaza["domain"] == domain:
                silinen = self.config["magazalar"].pop(i)
                self.kaydet()
                return f"{silinen['platform']} ({domain}) sistemden silindi."
        return f"{domain} mağazası bulunamadı."
    
    def urun_ekle(self, urun_bilgisi: Dict[str, Any]) -> str:
        """
        Ürün havuzuna yeni ürün ekler.
        
        Args:
            urun_bilgisi: Ürün bilgileri sözlüğü
            
        Returns:
            str: İşlem sonucu mesajı
        """
        urun_bilgisi["ekleme_tarihi"] = datetime.now().isoformat()
        self.config["urun_havuzu"].append(urun_bilgisi)
        self.kaydet()
        return f"Ürün başarıyla eklendi: {urun_bilgisi.get('urun_adi', 'Bilinmiyor')}"
    
    def iban_ekle(self, iban: str, sahibi: str) -> str:
        """
        IBAN havuzuna yeni IBAN ekler.
        
        Args:
            iban: IBAN numarası
            sahibi: IBAN sahibi
            
        Returns:
            str: İşlem sonucu mesajı
        """
        iban_bilgisi = {
            "iban": iban,
            "sahibi": sahibi,
            "ekleme_tarihi": datetime.now().isoformat(),
            "durum": "Aktif"
        }
        self.config["iban_havuzu"].append(iban_bilgisi)
        self.kaydet()
        return f"IBAN başarıyla eklendi: {iban}"
    
    def trm_ana_iban_ayarla(self, iban: str, sahibi: str) -> str:
        """
        TRM Ana IBAN olarak ana gelir hesabını ayarlar.
        Bu IBAN, tüm sistemin ana tahsilat ve ödeme merkezi olarak tanımlanır.
        
        Args:
            iban: Ana IBAN numarası
            sahibi: IBAN sahibi
            
        Returns:
            str: İşlem sonucu mesajı
        """
        ana_iban_bilgisi = {
            "iban": iban,
            "sahibi": sahibi,
            "tur": "TRM_ANA_IBAN",
            "aciklama": "Ana Tahsilat ve Ödeme Merkezi",
            "komisyon_akisi_kilitli": True,
            "ekleme_tarihi": datetime.now().isoformat(),
            "durum": "Aktif"
        }
        
        self.config["trm_ana_iban"] = ana_iban_bilgisi
        self.kaydet()
        return f"TRM Ana IBAN başarıyla ayarlandı: {iban} - Ana tahsilat ve ödeme merkezi olarak tanımlandı."
    
    def api_entegrasyonu_ekle(self, platform: str, api_url: str, api_anahtari: str, 
                              api_tipi: str = "REST") -> str:
        """
        Yeni API entegrasyonu ekler.
        
        Args:
            platform: Platform adı
            api_url: API URL adresi
            api_anahtari: API anahtarı
            api_tipi: API tipi (REST, GraphQL, SOAP)
            
        Returns:
            str: İşlem sonucu mesajı
        """
        entegrasyon = {
            "platform": platform,
            "api_url": api_url,
            "api_anahtari": api_anahtari,
            "api_tipi": api_tipi,
            "durum": "Aktif",
            "entegrasyon_tarihi": datetime.now().isoformat()
        }
        self.config["api_entegrasyonlari"].append(entegrasyon)
        self.kaydet()
        return f"{platform} API entegrasyonu başarıyla eklendi."
    
    def sistem_durumu(self) -> Dict[str, Any]:
        """
        Sistem durum raporu döndürür.
        
        Returns:
            Dict: Sistem durumu bilgileri
        """
        return {
            "trm_sistem_aktif": self.config.get("trm_sistem_aktif", True),
            "toplam_magaza_sayisi": len(self.config.get("magazalar", [])),
            "toplam_urun_sayisi": len(self.config.get("urun_havuzu", [])),
            "toplam_iban_sayisi": len(self.config.get("iban_havuzu", [])),
            "toplam_api_entegrasyonu": len(self.config.get("api_entegrasyonlari", [])),
            "sistem_bilgisi": self.config.get("sistem_bilgisi", {})
        }
    
    def kaydet(self):
        """Konfigürasyonu dosyaya kaydeder"""
        with open(self.config_dosyasi, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    entegrator = MagazaVeTRMEntegrasyonu()
    
    # TRM Ana IBAN Ayarlama
    print("--- TRM ANA IBAN AYARLANIYOR ---")
    ana_iban_durum = entegrator.trm_ana_iban_ayarla(
        iban="TR670020500009540781500003",
        sahibi="TRM Ticari Ekosistem TRM Ana Hesap"
    )
    print(ana_iban_durum)
    
    # Kendi Mağazamızın Kaydı (200.000+ ürün kapasitesi ile)
    print("\n--- MAĞAZA ENTEGRASYONU ---")
    durum = entegrator.magaza_ekle(
        platform_adi="Trend Ürünler Market",
        domain="trendurunlermarket.com",
        api_anahtari="TRM_SECURE_TOKEN_2026",
        iban="TR670020500009540781500003",
        urun_sayisi=200000,
        ulke="TR"
    )
    print(durum)
    
    # Sistem Durumu
    print("\n--- SİSTEM DURUMU ---")
    print(json.dumps(entegrator.sistem_durumu(), indent=2, ensure_ascii=False))
    
    # TRM Ana IBAN Bilgisi
    print("\n--- TRM ANA IBAN BİLGİSİ ---")
    print(json.dumps(entegrator.config.get("trm_ana_iban", {}), indent=2, ensure_ascii=False))
    
    # Örnek API Entegrasyonu
    api_durum = entegrator.api_entegrasyonu_ekle(
        platform="Trend Ürünler Market",
        api_url="https://api.trendurunlermarket.com/v1",
        api_anahtari="TRM_SECURE_TOKEN_2026",
        api_tipi="REST"
    )
    print(f"\n{api_durum}")
