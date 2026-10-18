# -*- coding: utf-8 -*-
"""
TRM - Nirvana Muhafız Ajanı
Odak: 7/24 sistem güvenliği, hata önleme ve koruma kalkanı
"""
import os
import json
import pandas as pd
from datetime import datetime
import logging

class NirvanaMuhafizAjani:
    def __init__(self):
        self.output_file = "nirvana_guvenlik_loglari.json"
        self.excel_file = "NIRVANA_GUVENLIK_RAPORU.xlsx"
        
        # Güvenlik loglama sistemi
        logging.basicConfig(
            filename='nirvana_guvenlik.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('NirvanaMuhafiz')
        
        # Tehdit seviyeleri
        self.tehdit_seviyeleri = {
            "CRITICAL": "Kritik - Acil Müdahale Gerekli",
            "HIGH": "Yüksek - Hızlı Önlem Alınmalı",
            "MEDIUM": "Orta - İzleme ve Analiz Gerekli",
            "LOW": "Düşük - Bilgilendirme",
            "INFO": "Bilgi - Sistem Durumu"
        }
        
        # Sistem bileşenleri için güvenlik kontrolleri
        self.sistem_bilesenleri = {
            "veritabani": {"durum": "aktif", "son_kontrol": None},
            "api": {"durum": "aktif", "son_kontrol": None},
            "dosya_sistemi": {"durum": "aktif", "son_kontrol": None},
            "kullanici_yonetimi": {"durum": "aktif", "son_kontrol": None}
        }

    def sistem_kontrolu_yap(self):
        """
        Tüm sistem bileşenlerini kontrol eder ve güvenlik durumu raporlar.
        """
        kontrol_sonuclari = []
        simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for bilesen, durum in self.sistem_bilesenleri.items():
            # Simüle edilmiş kontrol
            kontrol_basarili = True
            mesaj = f"{bilesen.capitalize()} bileşeni normal çalışıyor."
            tehdit_seviyesi = "INFO"
            
            # Rastgele hata simülasyonu (gerçek sistemde gerçek kontroller yapılır)
            if bilesen == "veritabani" and os.path.exists("trm_veritabani.db"):
                dosya_boyutu = os.path.getsize("trm_veritabani.db")
                if dosya_boyutu > 10 * 1024 * 1024:  # 10MB'den büyükse uyarı
                    kontrol_basarili = False
                    mesaj = f"Veritabanı dosya boyutu çok büyük: {dosya_boyutu / 1024 / 1024:.2f} MB"
                    tehdit_seviyesi = "MEDIUM"
            
            kontrol_sonuclari.append({
                "Bilesen": bilesen,
                "Durum": "AKTIF" if kontrol_basarili else "UYARI",
                "Mesaj": mesaj,
                "Tehdit_Seviyesi": tehdit_seviyesi,
                "Kontrol_Zamani": simdi
            })
            
            # Log kaydı
            self.logger.info(f"{bilesen} kontrolü: {tehdit_seviyesi} - {mesaj}")
        
        return kontrol_sonuclari

    def guvenlik_olayi_kaydet(self, olay_turu, aciklama, kaynak, tehdit_seviyesi="MEDIUM"):
        """
        Güvenlik olayını kaydeder ve loglar.
        """
        olay = {
            "Olay_ID": f"SEC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "Olay_Turu": olay_turu,
            "Aciklama": aciklama,
            "Kaynak": kaynak,
            "Tehdit_Seviyesi": tehdit_seviyesi,
            "Olay_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Durum": "INCeleniyor"
        }
        
        # Log kaydı
        log_mesaji = f"{tehdit_seviyesi} - {olay_turu}: {aciklama} (Kaynak: {kaynak})"
        if tehdit_seviyesi in ["CRITICAL", "HIGH"]:
            self.logger.error(log_mesaji)
        elif tehdit_seviyesi == "MEDIUM":
            self.logger.warning(log_mesaji)
        else:
            self.logger.info(log_mesaji)
        
        return olay

    def hata_onleme_analizi(self, hata_mesaji, hata_kaynagi):
        """
        Hata analizi yaparak önleyici tedbirler önerir.
        """
        oneriler = []
        
        if "dosya" in hata_mesaji.lower() and "bulunamadi" in hata_mesaji.lower():
            oneriler.append("Dosya yolunu kontrol edin ve gerekirse yeniden oluşturun.")
            oneriler.append("Otomatik yedekleme sistemini aktif edin.")
        
        elif "json" in hata_mesaji.lower() and "decode" in hata_mesaji.lower():
            oneriler.append("JSON dosyası bozuk olabilir. Yedekten geri yükleyin.")
            oneriler.append("Veri doğrulama mekanizmasını güçlendirin.")
        
        elif "permission" in hata_mesaji.lower() or "yetki" in hata_mesaji.lower():
            oneriler.append("Dosya izinlerini kontrol edin.")
            oneriler.append("Kullanıcı yetkilerini gözden geçirin.")
        
        elif "memory" in hata_mesaji.lower() or "bellek" in hata_mesaji.lower():
            oneriler.append("Sistem belleğini temizleyin.")
            oneriler.append("Büyük veri setlerini parçalara bölün.")
        
        else:
            oneriler.append("Hata kaynağını detaylı analiz edin.")
            oneriler.append("Sistem loglarını inceleyin.")
        
        return oneriler

    def koruma_kalkani_olustur(self, kritik_dosyalar):
        """
        Kritik dosyalar için koruma kalkanı oluşturur.
        """
        koruma_raporu = {
            "Kalkan_Olusturma_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Kritik_Dosya_Sayisi": len(kritik_dosyalar),
            "Koruma_Durumu": "AKTIF"
        }
        
        dosya_durumlari = []
        for dosya in kritik_dosyalar:
            dosya_var = os.path.exists(dosya)
            dosya_durumlari.append({
                "Dosya": dosya,
                "Var_Mi": "Evet" if dosya_var else "Hayır",
                "Koruma_Seviyesi": "YÜKSEK" if dosya_var else "ORTA"
            })
        
        koruma_raporu["Dosya_Durumlari"] = dosya_durumlari
        
        return koruma_raporu

    def raporu_arsivle(self, yeni_kayitlar):
        """Güvenlik kayıtlarını arşive işler."""
        mevcut_veriler = []
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                try:
                    mevcut_veriler = json.load(f)
                except json.JSONDecodeError:
                    mevcut_veriler = []
                    
        mevcut_veriler.extend(yeni_kayitlar)
        
        # JSON Kayıt
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(mevcut_veriler, f, ensure_ascii=False, indent=4)
            
        # Excel Raporu Çıktısı
        df = pd.DataFrame(mevcut_veriler)
        df.to_excel(self.excel_file, index=False)
        
        return True
