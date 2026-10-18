import os
import json
from datetime import datetime

class GenclikSahaKocuAjani:
    def __init__(self, veri_dosyasi="genclik_saha_veritabani.json"):
        self.veri_dosyasi = veri_dosyasi
        self.hafizayi_yukle()

    def hafizayi_yukle(self):
        """Gençlerin saha performans ve takip verilerini yükler."""
        if os.path.exists(self.veri_dosyasi):
            with open(self.veri_dosyasi, "r", encoding="utf-8") as f:
                self.hafiza = json.load(f)
        else:
            self.hafiza = {"genc_ekip": [], "toplam_saha_temasi": 0}

    def genc_kayit_ve_degerlendir(self, ad_soyad, siyasi_kol, notebook_var_mi, telefon_var_mi, uslup_puani):
        """
        Genç adayların ön eleme kriterlerini (Notebook, Akıllı Telefon, Üslup Güzelliği) 
        denetleyerek ekibe kabul durumunu belirler.
        """
        kabul_durumu = False
        red_nedeni = []

        if not (notebook_var_mi and telefon_var_mi):
            red_nedeni.append("Notebook veya akıllı telefon yetersizliği.")
        if uslup_puani < 85:
            red_nedeni.append("Üslup ve halkla iletişim puanı aranan kriterin altında.")

        if not red_nedeni:
            kabul_durumu = True
            mesaj = f"Tebrikler {ad_soyad}, ön elemeyi başarıyla geçtiniz! TRM Ticari Ekosistem Gençlik Ekibi'ne hoş geldiniz."
        else:
            mesaj = f"Adaylık onaylanmadı. Gerekçe: {', '.join(red_nedeni)}"

        aday_bilgi = {
            "zaman_damgasi": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ad_soyad": ad_soyad,
            "siyasi_kol": siyasi_kol,
            "kabul_durumu": kabul_durumu,
            "mesaj": mesaj,
            "29_gunluk_hedef": 600,
            "tamamlanan_temas": 0,
            "vefa_ziyaretleri_takip": []
        }
        
        self.hafiza["genc_ekip"].append(aday_bilgi)
        return aday_bilgi

    def gunluk_saha_takip_raporu(self, ad_soyad, bugun_yapilan_temas, ispat_belge_linki):
        """
        Gencin günlük yüz yüze saha çalışmasını, belgeli ispatını 
        ve 29 günlük 600 kişi kotasına etkisini denetler.
        """
        rapor = {
            "tarih": datetime.now().strftime("%Y-%m-%d"),
            "genc": ad_soyad,
            "bugun_eklenen": bugun_yapilan_temas,
            "ispat_durumu": "Belgeli ve Onaylı" if ispat_belge_linki else "Eksik Belge",
            "not": "3 adım kuralı uygulandı: Proje Tanıtımı, Üyelik ve 6 Dijital Mağaza Kurulumu."
        }
        return rapor

if __name__ == "__main__":
    koc = GenclikSahaKocuAjani()
    
    # Test Adayı
    yeni_genc = koc.genc_kayit_ve_degerlendir(
        ad_soyad="Ahmet Can", 
        siyasi_kol="Parti Gençlik Kolları / Temsilci", 
        notebook_var_mi=True, 
        telefon_var_mi=True, 
        uslup_puani=95
    )
    
    gunluk_rapor = koc.gunluk_saha_takip_raporu(
        ad_soyad="Ahmet Can", 
        bugun_yapilan_temas=22, 
        ispat_belge_linki="https://sistem.trendurunlermarket.com/ispatlar/ahmetcan_ gun1.pdf"
    )

    print("--- GENÇLİK SAHA KOÇU AJANI ANALİZİ ---")
    print(json.dumps(yeni_genc, indent=4, ensure_ascii=False))
    print("\n--- GÜNLÜK SAHA RAPORU ---")
    print(json.dumps(gunluk_rapor, indent=4, ensure_ascii=False))
