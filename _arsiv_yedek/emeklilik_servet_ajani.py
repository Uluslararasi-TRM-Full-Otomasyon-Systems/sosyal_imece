# -*- coding: utf-8 -*-
"""
TRM TICARI EKOSISTEMI - Güvenli Emeklilik Koruma Ajanı
Odak: 55 yaş üstü bireylerin anaparasını enflasyona karşı korumak ve düzenli pasif gelir/temettü projeksiyonu sunmak
"""
import os
import json
import pandas as pd
from datetime import datetime

class GuvenliEmeklilikKorumaAjani:
    def __init__(self):
        self.output_file = "guvenli_emeklilik_koruma_arsivi.json"
        self.excel_file = "GUVENLI_EMEKLILIK_KORUMA_RAPORU.xlsx"
        
        # Güvenli koruma araçları ve temettü oranları (Konservatif yaklaşım)
        self.koruma_araclari = {
            "Devlet Tahvili (Kira Sertifikası)": {
                "yillik_getiri": 0.28,  # %28 yıllık getiri (güncel piyasa)
                "risk_seviyesi": "Çok Düşük",
                "koruma_notu": "Devlet garantili, enflasyon korumalı"
            },
            "Altın (Gram Altın/Dolar Bazlı)": {
                "yillik_getiri": 0.35,  # %35 yıllık getiri (geçmiş performans)
                "risk_seviyesi": "Düşük",
                "koruma_notu": "Geleneksel güvenli liman, enflasyon karşıtı"
            },
            "Temettü Ödeyen BIST 30 Endeksi": {
                "yillik_getiri": 0.25,  # %25 yıllık temettü + değer artışı
                "risk_seviyesi": "Orta-Düşük",
                "koruma_notu": "Düzenli temettü, uzun vadeli koruma"
            },
            "Kira Geliri (Gayrimenkul)": {
                "yillik_getiri": 0.18,  # %18 yıllık kira getirisi
                "risk_seviyesi": "Düşük",
                "koruma_notu": "Sabit pasif gelir, varlık koruması"
            }
        }

    def emeklilik_projeksiyonu_hesapla(self, yas, anapara, tahmini_enflasyon, yil_suresi):
        """
        55 yaş üstü birey için anapara koruma projeksiyonu hesaplar.
        Enflasyon etkisini ve pasif gelir akışını gösterir.
        """
        yas = int(yas)
        anapara = float(anapara)
        enflasyon = float(tahmini_enflasyon) / 100
        yil = int(yil_suresi)
        
        if yas < 55:
            return {"hata": "Bu ajan 55 yaş üstü bireyler için tasarlanmıştır."}
        
        projeksiyonlar = []
        
        for araclar, veriler in self.koruma_araclari.items():
            yillik_getiri = veriler["yillik_getiri"]
            risk_seviyesi = veriler["risk_seviyesi"]
            koruma_notu = veriler["koruma_notu"]
            
            # Her yıl için projeksiyon
            yillik_detaylar = []
            guncel_anapara = anapara
            
            for yil_sayisi in range(1, yil + 1):
                # Enflasyon etkisi
                enflasyon_kaybi = guncel_anapara * enflasyon
                # Getiri kazancı
                getiri_kazanci = guncel_anapara * yillik_getiri
                # Net değişim
                net_degisim = getiri_kazanci - enflasyon_kaybi
                guncel_anapara += net_degisim
                
                yillik_detaylar.append({
                    "Yil": yil_sayisi,
                    "Baslangic_Tutar": round(guncel_anapara - net_degisim, 2),
                    "Enflasyon_Kaybi": round(enflasyon_kaybi, 2),
                    "Getiri_Kazanci": round(getiri_kazanci, 2),
                    "Net_Degisim": round(net_degisim, 2),
                    "Son_Tutar": round(guncel_anapara, 2)
                })
            
            # Risk uyarısı oluştur
            risk_uyarisi = self.risk_uyarisi_olustur(risk_seviyesi, araclar)
            
            projeksiyonlar.append({
                "Kisi_Yasi": yas,
                "Baslangic_Anapara_Tl": anapara,
                "Tahmini_Enflasyon": f"%{tahmini_enflasyon}",
                "Koruma_Araci": araclar,
                "Risk_Seviyesi": risk_seviyesi,
                "Yillik_Getiri_Orani": f"%{yillik_getiri * 100}",
                "Koruma_Notu": koruma_notu,
                "Risk_Uyarisi": risk_uyarisi,
                "Proje_Yil_Suresi": yil,
                "Yillik_Detaylar": yillik_detaylar,
                "Son_Tutar_Tl": round(guncel_anapara, 2),
                "Toplam_Getiri_Tl": round(guncel_anapara - anapara, 2),
                "Hesaplama_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return projeksiyonlar

    def risk_uyarisi_olustur(self, risk_seviyesi, arac_adi):
        """Risk seviyesine göre uyarı mesajı oluşturur."""
        if risk_seviyesi == "Çok Düşük":
            return f"✅ {arac_adi}: Devlet garantili, minimum risk. Anapara koruması yüksek."
        elif risk_seviyesi == "Düşük":
            return f"⚠️ {arac_adi}: Düşük risk seviyesi. Uzun vadeli koruma için uygun."
        elif risk_seviyesi == "Orta-Düşük":
            return f"⚠️ {arac_adi}: Orta-düşük risk. Kısa vadeli dalgalanmalar olabilir, uzun vadeli koruma sağlar."
        else:
            return f"❌ {arac_adi}: Dikkatli kullanım önerilir."

    def raporu_arsivle(self, yeni_projeksiyonlar):
        """Hesaplanan emeklilik projeksiyonlarını arşive işler."""
        mevcut_veriler = []
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                try:
                    mevcut_veriler = json.load(f)
                except json.JSONDecodeError:
                    mevcut_veriler = []
                    
        mevcut_veriler.extend(yeni_projeksiyonlar)
        
        # JSON Kayıt
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(mevcut_veriler, f, ensure_ascii=False, indent=4)
            
        # Excel Raporu Çıktısı
        df_listesi = []
        for proj in yeni_projeksiyonlar:
            yillik_df = pd.DataFrame(proj["Yillik_Detaylar"])
            yillik_df["Kisi_Yasi"] = proj["Kisi_Yasi"]
            yillik_df["Koruma_Araci"] = proj["Koruma_Araci"]
            yillik_df["Risk_Seviyesi"] = proj["Risk_Seviyesi"]
            yillik_df["Koruma_Notu"] = proj["Koruma_Notu"]
            yillik_df["Risk_Uyarisi"] = proj["Risk_Uyarisi"]
            df_listesi.append(yillik_df)
        
        if df_listesi:
            final_df = pd.concat(df_listesi, ignore_index=True)
            final_df.to_excel(self.excel_file, index=False)
        
        return True
