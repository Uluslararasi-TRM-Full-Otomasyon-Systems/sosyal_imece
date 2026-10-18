#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Veri Kaynakları Yöneticisi
TRM Ticari Ekosistem projesi için resmi kaynakları, Telegram gruplarını ve veri toplama kanallarını yöneten modül
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class VeriKaynaklariYoneticisi:
    def __init__(self, config_dosyasi="veri_kaynaklari_config.json"):
        self.config_dosyasi = config_dosyasi
        self.config = self.config_yukle()
        
    def config_yukle(self) -> Dict[str, Any]:
        """Veri kaynakları konfigürasyonunu yükler"""
        varsayilan_config = {
            "resmi_kaynaklar": [],
            "telegram_gruplari": [],
            "blog_kaynaklari": [],
            "veri_besleme_katmani": {
                "urun_gorselleri": True,
                "urun_metinleri": True,
                "video_materyalleri": True,
                "kullanici_yorumlari": True
            },
            "sistem_bilgisi": {
                "versiyon": "1.0.0",
                "olusturma_tarihi": datetime.now().isoformat(),
                "son_guncelleme": datetime.now().isoformat()
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
    
    def resmi_kaynak_ekle(self, kaynak_adi: str, url: str, kaynak_turu: str = "magaza") -> str:
        """
        Resmi kaynak ekler
        
        Args:
            kaynak_adi: Kaynak adı
            url: Kaynak URL adresi
            kaynak_turu: Kaynak türü (magaza, blog, diger)
            
        Returns:
            str: İşlem sonucu mesajı
        """
        kaynak = {
            "kaynak_adi": kaynak_adi,
            "url": url,
            "kaynak_turu": kaynak_turu,
            "durum": "Aktif",
            "ekleme_tarihi": datetime.now().isoformat()
        }
        
        self.config["resmi_kaynaklar"].append(kaynak)
        self.kaydet()
        return f"{kaynak_adi} başarıyla resmi kaynaklara eklendi."
    
    def telegram_grubu_ekle(self, grup_adi: str, url: str, grup_turu: str = "duyuru") -> str:
        """
        Telegram grubu ekler
        
        Args:
            grup_adi: Grup adı
            url: Grup URL adresi
            grup_turu: Grup türü (duyuru, tedarikci, yorumlar, stoksuz_satis)
            
        Returns:
            str: İşlem sonucu mesajı
        """
        grup = {
            "grup_adi": grup_adi,
            "url": url,
            "grup_turu": grup_turu,
            "durum": "Aktif",
            "ekleme_tarihi": datetime.now().isoformat()
        }
        
        self.config["telegram_gruplari"].append(grup)
        self.kaydet()
        return f"{grup_adi} Telegram grubu başarıyla eklendi."
    
    def blog_kaynagi_ekle(self, blog_adi: str, url: str, kategori: str = "genel") -> str:
        """
        Blog kaynağı ekler
        
        Args:
            blog_adi: Blog adı
            url: Blog URL adresi
            kategori: Blog kategorisi
            
        Returns:
            str: İşlem sonucu mesajı
        """
        blog = {
            "blog_adi": blog_adi,
            "url": url,
            "kategori": kategori,
            "durum": "Aktif",
            "ekleme_tarihi": datetime.now().isoformat()
        }
        
        self.config["blog_kaynaklari"].append(blog)
        self.kaydet()
        return f"{blog_adi} blog kaynağı başarıyla eklendi."
    
    def veri_besleme_ayari_guncelle(self, ayar_adi: str, durum: bool) -> str:
        """
        Veri besleme ayarını günceller
        
        Args:
            ayar_adi: Ayar adı
            durum: Ayar durumu
            
        Returns:
            str: İşlem sonucu mesajı
        """
        if ayar_adi in self.config["veri_besleme_katmani"]:
            self.config["veri_besleme_katmani"][ayar_adi] = durum
            self.config["sistem_bilgisi"]["son_guncelleme"] = datetime.now().isoformat()
            self.kaydet()
            return f"{ayar_adi} ayarı {durum} olarak güncellendi."
        return f"{ayar_adi} ayarı bulunamadı."
    
    def kaynaklari_listele(self, kaynak_turu: str = None) -> List[Dict[str, Any]]:
        """
        Kaynakları listeler
        
        Args:
            kaynak_turu: Kaynak türü (None ise tüm kaynaklar)
            
        Returns:
            List: Kaynak listesi
        """
        if kaynak_turu == "resmi":
            return self.config["resmi_kaynaklar"]
        elif kaynak_turu == "telegram":
            return self.config["telegram_gruplari"]
        elif kaynak_turu == "blog":
            return self.config["blog_kaynaklari"]
        else:
            return {
                "resmi_kaynaklar": self.config["resmi_kaynaklar"],
                "telegram_gruplari": self.config["telegram_gruplari"],
                "blog_kaynaklari": self.config["blog_kaynaklari"]
            }
    
    def sistem_durumu(self) -> Dict[str, Any]:
        """
        Sistem durum raporu döndürür
        
        Returns:
            Dict: Sistem durumu bilgileri
        """
        return {
            "toplam_resmi_kaynak": len(self.config["resmi_kaynaklar"]),
            "toplam_telegram_grubu": len(self.config["telegram_gruplari"]),
            "toplam_blog_kaynagi": len(self.config["blog_kaynaklari"]),
            "veri_besleme_katmani": self.config["veri_besleme_katmani"],
            "sistem_bilgisi": self.config["sistem_bilgisi"]
        }
    
    def kaydet(self):
        """Konfigürasyonu dosyaya kaydeder"""
        with open(self.config_dosyasi, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    yoneticisi = VeriKaynaklariYoneticisi()
    
    # Resmi Kaynaklar
    print("--- RESMİ KAYNAKLAR EKLENİYOR ---")
    yoneticisi.resmi_kaynak_ekle(
        kaynak_adi="Trend Ürünler Market",
        url="https://www.trendurunlermarket.com",
        kaynak_turu="magaza"
    )
    
    # Blog Kaynakları
    print("\n--- BLOG KAYNAKLARI EKLENİYOR ---")
    yoneticisi.blog_kaynagi_ekle(
        blog_adi="Fırsat Blok Blog",
        url="https://magaza.magazanolsun.com/FirsatBlok",
        kategori="firsat"
    )
    
    # Telegram Grupları
    print("\n--- TELEGRAM GRUPLARI EKLENİYOR ---")
    yoneticisi.telegram_grubu_ekle(
        grup_adi="MagazaNolsun Resmi",
        url="https://t.me/magazanolsunresmi",
        grup_turu="duyuru"
    )
    
    yoneticisi.telegram_grubu_ekle(
        grup_adi="Tedarikçi Grubu 1",
        url="https://t.me/+RJlMIxUcT1EUaSl7",
        grup_turu="tedarikci"
    )
    
    yoneticisi.telegram_grubu_ekle(
        grup_adi="Tedarikçi Grubu 2",
        url="https://t.me/joinchat/NjrBgUSZTCMu2gKyZlNVvg",
        grup_turu="tedarikci"
    )
    
    yoneticisi.telegram_grubu_ekle(
        grup_adi="Stoksuz Satış & Ürün Yorumları",
        url="https://t.me/stoksuzsatisyorumlari",
        grup_turu="yorumlar"
    )
    
    # Sistem Durumu
    print("\n--- SİSTEM DURUMU ---")
    print(json.dumps(yoneticisi.sistem_durumu(), indent=2, ensure_ascii=False))
    
    # Tüm Kaynaklar
    print("\n--- TÜM KAYNAKLAR ---")
    print(json.dumps(yoneticisi.kaynaklari_listele(), indent=2, ensure_ascii=False))
