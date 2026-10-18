import time

class TRMHarikaGumrukMuhafizi:
    def __init__(self):
        self.ajan_adi = "TRM KVKK Uyumlu Akıllı Gümrük Ajanı"
        self.turkis_yoksulluk_siniri = 114576.0

    def basvuru_sorgula(self, form_verisi):
        print(f"\n=================== [{self.ajan_adi}] ===================")
        print(f"📋 Başvuru Tipi Denetimi: {form_verisi['basvuru_sahibi_tipi']}")

        # 1. KURAL: REFAKATÇİ BAĞIMLI ENGELLİ KONTROLÜ
        if form_verisi['basvuru_sahibi_tipi'] == "REFAKATCI_UZERINDEN":
            print(f"♿ {form_verisi['refakatci_adi']}, ağır engelli yakını [{form_verisi['aday_adi']}] adına müracaat ediyor.")
            print("👁️ [RPA - Sanal Mouse Aktif]: Ekrandaki resmi engellilik raporu görsel olarak taranıyor...")
            
            # KVKK Uyumlu Ekran Okuma Simülasyonu (Veritabanına kaydetmeden sadece ekrandan okuma)
            if form_verisi['sanal_mouse_ekran_okuma']['raporda_agir_engelli_yaziyor_mu']:
                print("✅ Doğrulama Başarılı: Sanal göz ekrandaki barkodlu raporu teyit etti. Veri kaydedilmeden silindi.")
                print("🔒 ÖZEL ŞART: Refakatçi taahhütnamesi imzalatıldı. Ek iş yasağı aktiftir.")
                
                return {
                    "durum": "REFAKATCI_ONAY",
                    "mesaj": f"Sayın {form_verisi['refakatci_adi']}, yakınınız {form_verisi['aday_adi']} adına yaptığınız başvuru onaylanmıştır. Sistem harici hiçbir ek iş yapmama ve yaptırmama kuralı dahilinde refah payı engelli vatandaşımızın hesabına tanımlanmıştır."
                }
            else:
                return {"durum": "RED", "mesaj": "Ekran taramasında geçerli ağır engelli ibaresi bulunamadı."}

        # 2. KURAL: KENDİ BAŞINA BAŞVURANLAR İÇİN DİGİTAL OKUR-YAZARLIK VE TEMBELLİK FİLTRESİ
        if form_verisi['basvuru_sahibi_tipi'] == "KENDISI":
            print(f"👤 {form_verisi['aday_adi']} kendisi için başvuruyor.")
            
            # Tembellik ve Ek İş Yasağı Kontrolü
            if form_verisi['form_hizi_sn'] < 60:
                mesaj = (
                    f"Sayın {form_verisi['aday_adi']},\n"
                    "Başvurunuz form doldurma hızı ve baştan savma veri girişi nedeniyle reddedilmiştir.\n"
                    "TRM Ticari Dünyası ekosistemine dahil olabilmek için hiçbir ek iş yapmamanız, "
                    "sisteme tam odaklanmanız ve formu parmaklarınızı oynatarak, emek vererek doldurmanız gerekmektedir.\n"
                    "Kendinizi hazır hissettiğinizde 7 gün sonra tekrar müracaat edebilirsiniz."
                )
                return {"durum": "RED_EĞİTİM_ROTASI", "mesaj": mesaj}
            
            return {"durum": "STANDART_ONAY", "mesaj": "Müracaatınız kabul edildi. Sistem içi otonom görevleriniz hazırlanıyor."}

# --- KOZMİK ODA TESTİ ---
if __name__ == "__main__":
    muhafiz = TRMHarikaGumrukMuhafizi()

    # Senaryo: Rapor dolduramayacak durumdaki engelli adına annesinin başvurması
    engelli_ve_annesi = {
        "basvuru_sahibi_tipi": "REFAKATCI_UZERINDEN",
        "refakatci_adi": "Ayşe Yılmaz (Anne)",
        "aday_adi": "Ahmet Yılmaz (Ağır Engelli Evlat)",
        "basvuru_sahibi_maas": 0,
        "sanal_mouse_ekran_okuma": {
            "raporda_agir_engelli_yaziyor_mu": True,
            "rapor_orani": 90
        }
    }
    
    operasyon_sonucu = muhafiz.basvuru_sorgula(engelli_ve_annesi)
    print("\n[SİSTEM ÇIKTISI]:\n" + operasyon_sonucu["mesaj"])