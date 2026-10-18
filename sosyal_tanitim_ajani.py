# -*- coding: utf-8 -*-
"""
TRM TICARI EKOSISTEMI - Sosyal Tanıtım Ajanı
Odak: Otonom duyuru, raporlama ve tanıtım kuyruğu motoru
"""
import os
import json
import pandas as pd
from datetime import datetime

class SosyalTanitimAjani:
    def __init__(self):
        self.output_file = "sosyal_tanitim_kuyrugu.json"
        self.excel_file = "SOSYAL_TANITIM_RAPORU.xlsx"
        
        # Tanıtım kanalları
        self.tanitim_kanallari = {
            "web_sitesi": {"adi": "Web Sitesi", "durum": "aktif", "oncelik": "yuksek"},
            "sosyal_medya": {"adi": "Sosyal Medya", "durum": "aktif", "oncelik": "yuksek"},
            "eposta_bulteni": {"adi": "E-posta Bülteni", "durum": "aktif", "oncelik": "orta"},
            "whatsapp": {"adi": "WhatsApp", "durum": "aktif", "oncelik": "yuksek"},
            "basin": {"adi": "Basın", "durum": "beklemede", "oncelik": "dusuk"}
        }
        
        # Duyuru türleri
        self.duyuru_turleri = {
            "sistem_guncelleme": "Sistem Güncellemesi",
            "yeni_uye": "Yeni Üye Duyurusu",
            "etkinlik": "Etkinlik Duyurusu",
            "rapor": "Rapor Yayını",
            "acil": "Acil Duyuru",
            "genel": "Genel Bilgilendirme"
        }

    def duyuru_olustur(self, duyuru_turu, baslik, icerik, hedef_kanallar, oncelik="orta"):
        """
        Yeni duyuru oluşturur ve kuyruğa ekler.
        """
        duyuru = {
            "Duyuru_ID": f"DYR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "Duyuru_Turu": self.duyuru_turleri.get(duyuru_turu, duyuru_turu),
            "Baslik": baslik,
            "Icerik": icerik,
            "Hedef_Kanallar": hedef_kanallar,
            "Oncelik": oncelik,
            "Olusturma_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Durum": "Kuyrukta",
            "Yayinlanma_Zamani": None,
            "Goruntuleme_Sayisi": 0
        }
        
        return duyuru

    def rapor_olustur(self, rapor_turu, rapor_basligi, rapor_icerigi, hedef_kitle):
        """
        Rapor oluşturur ve dağıtım kuyruğuna ekler.
        """
        rapor = {
            "Rapor_ID": f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "Rapor_Turu": rapor_turu,
            "Rapor_Basligi": rapor_basligi,
            "Rapor_Icerigi": rapor_icerigi,
            "Hedef_Kitle": hedef_kitle,
            "Olusturma_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Durum": "Hazır",
            "Dağıtım_Durumu": "Beklemede"
        }
        
        return rapor

    def tanitim_kampanyasi_baslat(self, kampanya_adi, baslangic_tarihi, bitis_tarihi, kanallar, bütce):
        """
        Tanıtım kampanyası başlatır.
        """
        kampanya = {
            "Kampanya_ID": f"KMP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "Kampanya_Adi": kampanya_adi,
            "Baslangic_Tarihi": baslangic_tarihi,
            "Bitis_Tarihi": bitis_tarihi,
            "Kanallar": kanallar,
            "Bütce": bütce,
            "Durum": "Aktif",
            "Olusturma_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Ilerleme": "0%"
        }
        
        return kampanya

    def kuyrugu_isle(self, kuyruk_turu="duyuru"):
        """
        Kuyruktaki öğeleri işler (simülasyon).
        """
        islenen_ogeler = []
        
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                try:
                    kuyruk = json.load(f)
                except json.JSONDecodeError:
                    kuyruk = []
            
            # Kuyruk türüne göre filtrele
            filtreli_kuyruk = [k for k in kuyruk if kuyruk_turu in k.get("Duyuru_ID", "") or kuyruk_turu in k.get("Rapor_ID", "")]
            
            for ogeler in filtreli_kuyruk:
                if ogeler.get("Durum") == "Kuyrukta":
                    # İşleme simülasyonu
                    ogeler["Durum"] = "Yayınlandı"
                    ogeler["Yayinlanma_Zamani"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ogeler["Goruntuleme_Sayisi"] = 150  # Simüle edilmiş görüntüleme
                    islenen_ogeler.append(ogeler)
        
        return islenen_ogeler

    def istatistik_raporu_olustur(self):
        """
        Tanıtım istatistikleri raporu oluşturur.
        """
        istatistik = {
            "Raporlama_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Toplam_Duyuru": 0,
            "Toplam_Rapor": 0,
            "Toplam_Kampanya": 0,
            "Aktif_Kanallar": 0,
            "Toplam_Goruntuleme": 0
        }
        
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                try:
                    kuyruk = json.load(f)
                except json.JSONDecodeError:
                    kuyruk = []
            
            # İstatistikleri hesapla
            istatistik["Toplam_Duyuru"] = len([k for k in kuyruk if "DYR" in k.get("Duyuru_ID", "")])
            istatistik["Toplam_Rapor"] = len([k for k in kuyruk if "RPT" in k.get("Rapor_ID", "")])
            istatistik["Toplam_Kampanya"] = len([k for k in kuyruk if "KMP" in k.get("Kampanya_ID", "")])
            istatistik["Aktif_Kanallar"] = len([k for k, v in self.tanitim_kanallari.items() if v["durum"] == "aktif"])
            istatistik["Toplam_Goruntuleme"] = sum([k.get("Goruntuleme_Sayisi", 0) for k in kuyruk])
        
        return istatistik

    def raporu_arsivle(self, yeni_kayitlar):
        """Tanıtım kayıtlarını arşive işler."""
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
