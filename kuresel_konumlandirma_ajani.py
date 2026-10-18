# trm_agents/kuresel_konumlandirma_ajani.py
import json
import os

class KureselKonumlandirmaAjani:
    def __init__(self):
        self.ajanin_adi = "161. Akilli Konumlandirma ve Link Eslestirme Uzmani"
        self.komisyon_havuzu_dosyasi = "uluslararasi_affiliate_havuzu.json"
        self.katilimci_hesaplari_dosyasi = "katilimci_sosyal_medya_bilgileri.json"

    def katilimci_profilini_analiz_et(self, katilimci_id):
        """Katilimcinin sosyal medya hesabinin dilini ve ana kitlesini analiz eder."""
        # Burada pilot grubun (10 kisi) hesap parametreleri simule edilir
        # Ornegin: Instagram (Moda/Teknoloji) veya TikTok (Ev-Ofis Gerecleri)
        return {
            "hedef_cografya": "Global (US/EU)",
            "ana_odak_alani": "Dijital Donusum & Gunluk Pratik Cozumler",
            "hesap_dili": "Ingilizce / Cok Dilli"
        }

    def en_uygun_komisyonlu_urunu_sec(self, profil_ozellikleri):
        """Uluslararasi havuzdan en az zahmetle en yuksek dolar komisyonu getirecek linki secer."""
        # Magaza yonetimi YOK! Sadece yuksek donusumlu link eslestirme var.
        return {
            "urun_adi": "Otonom Ev-Ofis Bel Destegi (Ergonomik)",
            "affiliate_linki": "https://amazon.com/affiliate/trm_ticari_pilot01",
            "komisyon_orani": "%15",
            "tahmini_kazanc_dolar": "12.50 USD (Satis Basina)"
        }

    def otonom_sosyal_medya_icerigi_uret(self, urun_verisi):
        """Katilimcinin parmagini bile oynatmadan paylasabilecegi hazir reklam metni ve gorsel senaryosunu uretir."""
        metin = f"🚀 {urun_verisi['urun_adi']} ile tanisin! Evden calisirken bel agrilarina son. Link profilde! 👉 {urun_verisi['affiliate_linki']}"
        hashtagler = "#wfh #ergonomics #homeoffice #trmticari"
        return {
            "paylasim_metni": metin,
            "etiketler": hashtagler,
            "otonom_gorsel_senaryosu": "Arka planda rahat calisan bir insan, on planda urun vurgusu."
        }
