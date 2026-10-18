# -*- coding: utf-8 -*-
"""
TRM TICARI EKOSISTEMI - İtiraz ve Geri Bildirim Denetçi Ajanı
Görev: Üyelerin sistem kararlarına karşı yükledikleri gider fişlerini, faturaları 
veya haklılık beyanlarını otonom olarak inceler, doğrular ve katsayı güncellemesi önerir.
"""
import os
import json
import pandas as pd
from datetime import datetime

class ItirazDenetciAjani:
    def __init__(self):
        self.itiraz_arsiv_file = "itiraz_ve_denetim_arsivi.json"
        self.excel_rapor = "ITIRAZ_DENETIM_RAPORU.xlsx"

    def itiraz_degerlendir_ve_simule_et(self, uye_adi, sehir, itiraz_gerekcesi, harcama_turu, yuklenen_tutar, kanit_belge_adi):
        """
        Üyenin itirazını ve yüklediği kanıt belgesini analiz eder.
        Not: Canlı sistemde buraya OCR / Görsel işleme (GPT-4o Vision vb.) entegre edilir.
        Burada simülasyon mantığıyla analizi gerçekleştiriyoruz.
        """
        tutar = float(yuklenen_tutar)
        
        # Otonom Kriter ve Doğrulama Algoritması
        # Belirtilen harcama türüne göre mantıksal sınır kontrolü
        makul_mu = True
        ai_notu = "Belge başarıyla doğrulandı ve temel yaşam gideri kapsamında incelendi."
        
        if tutar <= 0:
            makul_mu = False
            ai_notu = "Hata: Geçersiz veya sıfır tutarlı belge beyan edildi."
        elif harcama_turu == "Kira" and tutar < 3000:
            makul_mu = False
            ai_notu = "Uyarı: Girilen kira bedeli piyasa gerçekliğinin çok altında, ek inceleme gerekiyor."
        
        # Sonuç Kararı
        durum = "Onaylandı - Katsayı Güncellemesine Eklendi" if makul_mu else "Reddedildi - Şüpheli / Yetersiz Kanıt"
        
        degerlendirme_sonucu = {
            "Id": f"ITR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Uye_Adi": uye_adi,
            "Sehir": sehir,
            "Harcama_Turu": harcama_turu,
            "Beyan_Edilen_Tutar_Tl": tutar,
            "Kanit_Belge": kanit_belge_adi,
            "AI_Analiz_Notu": ai_notu,
            "Karar": durum
        }
        
        return degerlendirme_sonucu

    def arsive_isle(self, yeni_itiraz):
        """İtiraz ve denetim sonuçlarını arşive ve excel tablosuna kaydeder."""
        mevcut = []
        if os.path.exists(self.itiraz_arsiv_file):
            with open(self.itiraz_arsiv_file, 'r', encoding='utf-8') as f:
                try:
                    mevcut = json.load(f)
                except json.JSONDecodeError:
                    mevcut = []
                    
        mevcut.append(yeni_itiraz)
        
        with open(self.itiraz_arsiv_file, 'w', encoding='utf-8') as f:
            json.dump(mevcut, f, ensure_ascii=False, indent=4)
            
        df = pd.DataFrame(mevcut)
        df.to_excel(self.excel_rapor, index=False)
        return True