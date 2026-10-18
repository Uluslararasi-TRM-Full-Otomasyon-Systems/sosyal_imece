# -*- coding: utf-8 -*-
"""
TRM TICARI EKOSISTEMI - Şehir Bazlı Ekonomi ve Refah Payı Analiz Ajanı (81 İl Entegrasyonu)
Mantık: Şehirlerin temel yaşam maliyetlerini hesaplar, üzerine %20 Refah Güvenlik/Adalet Payı ekleyerek 
net refah destek tutarlarını belirler.
"""
import os
import json
import pandas as pd
from datetime import datetime
from cografi_demografik_modul import CografiDemografikModul

class SehirBazliEkonomiAjani:
    def __init__(self):
        self.output_file = "sehir_refah_esikleri_arsivi.json"
        self.excel_file = "SEHIR_BAZLI_REFAH_RAPORU.xlsx"
        
        # Coğrafi demografik modülünü entegre et
        self.cografi_modul = CografiDemografikModul()
        
        # 81 il için ekonomik katsayılar (Coğrafi modülden dinamik olarak hesaplanır)
        self.sehir_katsayilari = self._sehir_katsayilari_olustur()
    
    def _sehir_katsayilari_olustur(self):
        """81 il için ekonomik katsayıları oluşturur."""
        katsayilar = {}
        
        for plaka, il_verisi in self.cografi_modul.turkiye_illeri.items():
            il_adi = il_verisi["il_adi"]
            ekonomik_seviye = il_verisi["ekonomik_seviye"]
            yogunluk = il_verisi["yogunluk"]
            
            # Ekonomik seviye ve yoğunluğa göre katsayı belirleme
            if ekonomik_seviye == "Çok Gelişmiş" and yogunluk == "Çok Yüksek":
                katsayi = 1.45  # İstanbul
            elif ekonomik_seviye == "Çok Gelişmiş" and yogunluk == "Yüksek":
                katsayi = 1.40  # Ankara, İzmir
            elif ekonomik_seviye == "Gelişmiş" and yogunluk == "Yüksek":
                katsayi = 1.35  # Antalya, Bursa, Kocaeli
            elif ekonomik_seviye == "Gelişmiş" and yogunluk == "Orta":
                katsayi = 1.30  # Gaziantep, Şanlıurfa, Diyarbakır
            elif ekonomik_seviye == "Gelişmiş" and yogunluk == "Düşük":
                katsayi = 1.25  # Muğla, Kayseri, Eskişehir
            elif ekonomik_seviye == "Orta" and yogunluk == "Orta":
                katsayi = 1.20  # Orta seviye şehirler
            elif ekonomik_seviye == "Orta" and yogunluk == "Düşük":
                katsayi = 1.15  # Kırsal şehirler
            elif ekonomik_seviye == "Düşük":
                katsayi = 1.10  # Gelişmekte olan bölgeler
            else:
                katsayi = 1.00  # Varsayılan
            
            katsayilar[il_adi] = katsayi
        
        return katsayilar

    def sehir_bazli_hesapla(self, yil, ay, baz_aclik_siniri):
        """
        Belirtilen baz açlık sınırını şehir katsayıları ile çarpar, 
        ardından kullanıcının talimatı olan +%20 Refah Güvenlik/Adalet Payını ekleyerek 
        şehir bazlı net refah destek tutarlarını hesaplar.
        """
        temel_baz = float(baz_aclik_siniri)
        hesaplanmis_sehir_verileri = []

        for sehir, katsayi in self.sehir_katsayilari.items():
            # O şehrin yaşam maliyeti
            sehir_maliyeti = temel_baz * katsayi
            
            # Kullanıcının belirlediği +%20 Adalet ve Emniyet Payı eklenmiş Hali
            net_imece_payi = sehir_maliyeti * 1.20  # %20 artış
            
            # Yoksulluk ve zenginlik bantları
            yoksulluk_siniri = net_imece_payi * 1.25

            hesaplanmis_sehir_verileri.append({
                "Donem": f"{yil}-{ay:02d}",
                "Sehir": sehir,
                "Sehir_Katsayisi": katsayi,
                "Baz_Maliyet_Tl": round(sehir_maliyeti, 2),
                "Net_Refah_Destek_Payi_Tl": round(net_imece_payi, 2), # Hesaplara gönderilecek tutar
                "Yoksulluk_Esigi_Tl": round(yoksulluk_siniri, 2),
                "Guncelleme_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        return hesaplanmis_sehir_verileri

    def raporu_arsivle(self, yeni_veriler):
        """Hesaplanan şehir bazlı raporları arşive işler."""
        mevcut_veriler = []
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                try:
                    mevcut_veriler = json.load(f)
                except json.JSONDecodeError:
                    mevcut_veriler = []
                    
        # Aynı döneme ait eski kayıtları temizle, yenilerini ekle
        donem = yeni_veriler[0]["Donem"]
        mevcut_veriler = [v for v in mevcut_veriler if v["Donem"] != donem]
        mevcut_veriler.extend(yeni_veriler)
        
        # JSON Kayıt
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(mevcut_veriler, f, ensure_ascii=False, indent=4)
            
        # Excel Raporu Çıktısı
        df = pd.DataFrame(mevcut_veriler)
        df.to_excel(self.excel_file, index=False)
        
        return True