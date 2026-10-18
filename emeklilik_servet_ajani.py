# -*- coding: utf-8 -*-
"""
TRM TICARI EKOSISTEMI - 81 İl Bazlı Çift Aşamalı Güvenli Emeklilik ve Adalet Refah Dağılım Ajanı
"""
import os
import json
import pandas as pd
from datetime import datetime

class GuvenliEmeklilikKorumaAjani:
    def __init__(self):
        self.output_file = "guvenli_emeklilik_koruma_arsivi.json"
        self.excel_file = "GUVENLI_EMEKLILIK_KORUMA_RAPORU.xlsx"
        
        self.il_katsayilari = {
            "İstanbul": 1.45, "Ankara": 1.40, "İzmir": 1.40, "Kocaeli": 1.38, "Bursa": 1.35,
            "Antalya": 1.35, "Adana": 1.32, "Mersin": 1.32, "Gaziantep": 1.30, "Konya": 1.30,
            "Tekirdağ": 1.35, "Sakarya": 1.32, "Eskişehir": 1.32, "Kayseri": 1.30, "Samsun": 1.30,
            "Trabzon": 1.28, "Balıkesir": 1.30, "Aydın": 1.32, "Muğla": 1.38, "Denizli": 1.30
        }
        
        self.tum_iller = [
            "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin", "Aydın", "Balıkesir",
            "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli",
            "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkâri",
            "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir",
            "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş", "Nevşehir",
            "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat",
            "Trabzon", "Tunceli", "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman",
            "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Düzce"
        ]

    def il_katsayi_getir(self, il_adi):
        return self.il_katsayilari.get(il_adi, 1.25)

    def imece_havuzu_degerlendir(self, toplam_ciro, komisyon_orani=0.30):
        return toplam_ciro * komisyon_orani

    def iki_asamali_refah_ve_zenginlik_dagitimi(self, imece_havuz_butcesi, il_adi, toplam_uye_sayisi, yas_55_ustu_nufus):
        """
        1. Aşama: Sistemdeki tüm kullanıcılara il bazlı enflasyon hesapları yapılarak 
                  temel refah payı + %20 refah payı dağıtılır.
        2. Aşama: Havuzda kalan gelir rakamı, sadece 55 yaş ve üzeri kişilere özel 
                  'refah zenginlik payı' olarak bölünür ve aktarılır.
        Zaman Damgası: Her ayın 01. günü saat 00:10.
        """
        carpan = self.il_katsayi_getir(il_adi)
        degerlenmis_havuz = imece_havuz_butcesi * carpan
        
        # Aşama 1: Genel Kullanıcılara Refah Payı + %20 Refah Payı (%70 bütçe ayrımı)
        asama_1_butce = degerlenmis_havuz * 0.70
        if toplam_uye_sayisi <= 0:
            kisi_basi_genel_pay = 0.0
        else:
            kisi_basi_genel_pay = asama_1_butce / toplam_uye_sayisi
            
        # Aşama 2: Kalan Havuz Geliri (%30 bütçe) -> Sadece 55 Yaş ve Üzeri Kişilere Refah Zenginlik Payı
        asama_2_kalan_butce = degerlenmis_havuz * 0.30
        if yas_55_ustu_nufus <= 0:
            kisi_basi_zenginlik_payi = 0.0
        else:
            kisi_basi_zenginlik_payi = asama_2_kalan_butce / yas_55_ustu_nufus
            
        # 55 yaş üstü bir kişinin toplam alacağı (Genel Pay + Zenginlik Payı)
        toplam_55_ustu_net_pay = kisi_basi_genel_pay + kisi_basi_zenginlik_payi
        
        aktarim_zaman_damgasi = "Her ayın 01. günü saat 00:10"
        
        sonuc = {
            "il": il_adi,
            "il_carpani": carpan,
            "ham_havuz": imece_havuz_butcesi,
            "degerlenmis_havuz": degerlenmis_havuz,
            "toplam_uye_sayisi": toplam_uye_sayisi,
            "yas_55_ustu_nufus": yas_55_ustu_nufus,
            "kisi_basi_genel_pay": kisi_basi_genel_pay,
            "kisi_basi_zenginlik_payi": kisi_basi_zenginlik_payi,
            "toplam_55_ustu_net_pay": toplam_55_ustu_net_pay,
            "aktarim_zamani": aktarim_zaman_damgasi
        }
        return sonuc

    def arshive_isle_ve_excel_kaydet(self, sonuc_verisi):
        mevcut_veriler = []
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    mevcut_veriler = json.load(f)
            except:
                mevcut_veriler = []
                
        sonuc_verisi["tarih"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mevcut_veriler.append(sonuc_verisi)
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(mevcut_veriler, f, ensure_ascii=False, indent=4)
            
        df = pd.DataFrame(mevcut_veriler)
        df.to_excel(self.excel_file, index=False)
        return self.excel_file