#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UTEYKDER Üye Kayıt AI Ajanı - TRM Ticari Dünyası Entegrasyonu
- Dinamik sorular ile form oluşturma
- DERBİS formatında Excel dışa aktarma
"""

import sys
import io
import json
import os
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict

# UTF-8 encoding fix for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UteykderUye:
    """UTEYKDER Üye Veri Yapısı"""
    ad: str
    soyad: str
    telefon: str
    email: str
    adres: str
    meslek: str
    tc_kimlik: str
    dogum_tarihi: str
    egitim_durumu: str
    il: str
    ilce: str
    kayit_tarihi: str
    uye_turu: str = "Fahri Üye"
    uye_no: str = ""

class UteykderUyeAjani:
    def __init__(self):
        self.uye_veritabani = "uteykder_fahri_uyeler.json"
        self.excel_dosyasi = "uteykder_derbis_listesi.xlsx"
        self.uye_sayaci = 0
        self.uye_veritabani_yukle()
    
    def dinamik_sorular(self) -> List[Dict]:
        """Dinamik form soruları listesi"""
        return [
            {
                "id": "ad",
                "label": "Ad",
                "type": "text",
                "zorunlu": True,
                "max_chars": 50,
                "placeholder": "Adınızı girin"
            },
            {
                "id": "soyad",
                "label": "Soyad",
                "type": "text",
                "zorunlu": True,
                "max_chars": 50,
                "placeholder": "Soyadınızı girin"
            },
            {
                "id": "tc_kimlik",
                "label": "TC Kimlik No",
                "type": "text",
                "zorunlu": True,
                "max_chars": 11,
                "placeholder": "11 haneli TC kimlik numarası",
                "pattern": r"^\d{11}$"
            },
            {
                "id": "dogum_tarihi",
                "label": "Doğum Tarihi",
                "type": "date",
                "zorunlu": True,
                "placeholder": "GG.AA.YYYY"
            },
            {
                "id": "telefon",
                "label": "Telefon",
                "type": "text",
                "zorunlu": True,
                "max_chars": 15,
                "placeholder": "05551234567"
            },
            {
                "id": "email",
                "label": "E-posta",
                "type": "email",
                "zorunlu": True,
                "max_chars": 100,
                "placeholder": "ornek@email.com"
            },
            {
                "id": "egitim_durumu",
                "label": "Eğitim Durumu",
                "type": "select",
                "zorunlu": True,
                "secenekler": [
                    "İlkokul",
                    "Ortaokul",
                    "Lise",
                    "Önlisans",
                    "Lisans",
                    "Yüksek Lisans",
                    "Doktora"
                ]
            },
            {
                "id": "meslek",
                "label": "Meslek",
                "type": "text",
                "zorunlu": True,
                "max_chars": 50,
                "placeholder": "Mevcut mesleğiniz"
            },
            {
                "id": "il",
                "label": "İl",
                "type": "select",
                "zorunlu": True,
                "secenekler": [
                    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya",
                    "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu",
                    "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır",
                    "Düzce", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep",
                    "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Iğdır", "Isparta", "İstanbul",
                    "İzmir", "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri",
                    "Kırıkkale", "Kırklareli", "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya",
                    "Manisa", "Mardin", "Mersin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu",
                    "Osmaniye", "Rize", "Sakarya", "Samsun", "Şanlıurfa", "Siirt", "Sinop",
                    "Sivas", "Şırnak", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Uşak",
                    "Van", "Yalova", "Yozgat", "Zonguldak"
                ]
            },
            {
                "id": "ilce",
                "label": "İlçe",
                "type": "text",
                "zorunlu": True,
                "max_chars": 50,
                "placeholder": "İlçe adı"
            },
            {
                "id": "adres",
                "label": "Açık Adres",
                "type": "textarea",
                "zorunlu": False,
                "max_chars": 200,
                "placeholder": "Tam adres bilgisi"
            }
        ]
    
    def uye_veritabani_yukle(self):
        """Üye veritabanını yükle"""
        try:
            if os.path.exists(self.uye_veritabani):
                with open(self.uye_veritabani, 'r', encoding='utf-8') as f:
                    uyeler = json.load(f)
                self.uye_sayaci = len(uyeler)
        except Exception as e:
            logger.error(f"Üye veritabanı yükleme hatası: {e}")
            self.uye_sayaci = 0
    
    def uye_no_uret(self):
        """Benzersiz üye numarası oluştur"""
        self.uye_sayaci += 1
        return f"UTEYKDER-{datetime.now().year}-{self.uye_sayaci:04d}"
    
    def uye_kaydet(self, uye: UteykderUye):
        """Üyeyi veritabanına kaydet"""
        try:
            uyeler = []
            if os.path.exists(self.uye_veritabani):
                with open(self.uye_veritabani, 'r', encoding='utf-8') as f:
                    uyeler = json.load(f)
            
            uye_dict = asdict(uye)
            uyeler.append(uye_dict)
            
            with open(self.uye_veritabani, 'w', encoding='utf-8') as f:
                json.dump(uyeler, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Üye başarıyla kaydedildi: {uye.uye_no}")
            return True
        except Exception as e:
            logger.error(f"❌ Üye kaydetme hatası: {e}")
            return False
    
    def derbis_excel_olustur(self):
        """DERBİS formatında Excel dosyası oluştur"""
        try:
            import pandas as pd
            
            if not os.path.exists(self.uye_veritabani):
                return False
            
            with open(self.uye_veritabani, 'r', encoding='utf-8') as f:
                uyeler = json.load(f)
            
            if not uyeler:
                return False
            
            # DERBİS formatına uygun DataFrame oluştur
            derbis_data = []
            for uye in uyeler:
                derbis_data.append({
                    "Üye No": uye.get("uye_no", ""),
                    "TC Kimlik": uye.get("tc_kimlik", ""),
                    "Ad": uye.get("ad", ""),
                    "Soyad": uye.get("soyad", ""),
                    "Doğum Tarihi": uye.get("dogum_tarihi", ""),
                    "Telefon": uye.get("telefon", ""),
                    "E-posta": uye.get("email", ""),
                    "Eğitim Durumu": uye.get("egitim_durumu", ""),
                    "Meslek": uye.get("meslek", ""),
                    "İl": uye.get("il", ""),
                    "İlçe": uye.get("ilce", ""),
                    "Adres": uye.get("adres", ""),
                    "Üye Türü": uye.get("uye_turu", ""),
                    "Kayıt Tarihi": uye.get("kayit_tarihi", "")
                })
            
            df = pd.DataFrame(derbis_data)
            df.to_excel(self.excel_dosyasi, index=False, engine='openpyxl')
            
            logger.info(f"✅ DERBİS Excel dosyası oluşturuldu: {self.excel_dosyasi}")
            return True
        except ImportError:
            logger.error("❌ openpyxl kütüphanesi yüklü değil")
            return False
        except Exception as e:
            logger.error(f"❌ Excel oluşturma hatası: {e}")
            return False
    
    def tum_uyeleri_listele(self):
        """Tüm üyeleri listele"""
        try:
            if os.path.exists(self.uye_veritabani):
                with open(self.uye_veritabani, 'r', encoding='utf-8') as f:
                    uyeler = json.load(f)
                return uyeler
            return []
        except Exception as e:
            logger.error(f"Üye listeleme hatası: {e}")
            return []

def main():
    """Test fonksiyonu"""
    print("🚀 UTEYKDER Üye Kayıt AI Ajanı Başlatılıyor...")
    print("=" * 60)
    
    ajan = UteykderUyeAjani()
    
    # Dinamik soruları göster
    print("📋 Dinamik Sorular:")
    for soru in ajan.dinamik_sorular():
        print(f"   - {soru['label']} ({soru['type']})")
    
    # Test kaydı
    sonuc = ajan.uye_kaydet(UteykderUye(
        ad="Ahmet",
        soyad="Yılmaz",
        tc_kimlik="12345678901",
        dogum_tarihi="01.01.1990",
        telefon="05551234567",
        email="ahmet@example.com",
        egitim_durumu="Lisans",
        meslek="Mühendis",
        il="İstanbul",
        ilce="Kadıköy",
        adres="İstanbul, Türkiye",
        kayit_tarihi=datetime.now().isoformat(),
        uye_no=ajan.uye_no_uret()
    ))
    
    print(f"Kayıt Sonucu: {sonuc}")
    
    # DERBİS Excel oluştur
    excel_sonuc = ajan.derbis_excel_olustur()
    print(f"Excel Sonucu: {excel_sonuc}")
    
    print("=" * 60)
    print("✅ Test tamamlandı!")

if __name__ == "__main__":
    main()
