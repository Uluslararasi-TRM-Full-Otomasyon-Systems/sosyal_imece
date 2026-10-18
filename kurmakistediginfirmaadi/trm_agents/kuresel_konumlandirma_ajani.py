# trm_agents/kuresel_konumlandirma_ajani.py
import json
import os

class KureselKonumlandirmaAjani:
    def __init__(self):
        self.ajanin_adi = "161. Akıllı Konumlandırma ve Link Eşleştirme Uzmanı"
        self.komisyon_havuzu_dosyasi = "uluslararasi_affiliate_havuzu.json"
        self.katilimci_hesaplari_dosyasi = "katilimci_sosyal_medya_bilgileri.json"

    def katilimci_profilini_analiz_et(self, katilimci_id):
        """Katılımcının sosyal medya hesabının dilini ve ana kitlesini analiz eder."""
        # Burada pilot grubun (10 kişi) hesap parametreleri simüle edilir
        # Örneğin: Instagram (Moda/Teknoloji) veya TikTok (Ev-Ofis Gereçleri)
        return {
            "hedef_cografya": "Global (US/EU)",
            "ana_odak_alani": "Dijital Dönüşüm & Günlük Pratik Çözümler",
            "hesap_dili": "İngilizce / Çok Dilli"
        }

    def en_uygun_komisyonlu_urunu_sec(self, profil_ozellikleri):
        """Uluslararası havuzdan en az zahmetle en yüksek dolar komisyonu getirecek linki seçer."""
        # Mağaza yönetimi YOK! Sadece yüksek dönüşümlü link eşleştirme var.
        return {
            "urun_adi": "Otonom Ev-Ofis Bel Desteği (Ergonomik)",
            "affiliate_linki": "https://amazon.com/affiliate/trm_ticari_pilot01",
            "komisyon_orani": "%15",
            "tahmini_kazanc_dolar": "12.50 USD (Satış Başına)"
        }

    def otonom_sosyal_medya_icerigi_uret(self, urun_verisi):
        """Katılımcının parmağını bile oynatmadan paylaşabileceği hazır reklam metni ve görsel senaryosunu üretir."""
        metin = f"🚀 {urun_verisi['urun_adi']} ile tanışın! Evden çalışırken bel ağrılarına son. Link profilde! 👉 {urun_verisi['affiliate_linki']}"
        hashtagler = "#wfh #ergonomics #homeoffice #trmticari"
        return {
            "paylasim_metni": metin,
            "etiketler": hashtagler,
            "otonom_gorsel_senaryosu": "Arka planda rahat çalışan bir insan, ön planda ürün vurgusu."
        }