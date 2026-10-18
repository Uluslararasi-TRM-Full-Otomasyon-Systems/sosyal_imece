import os
import json
from datetime import datetime

class TRMTicariIcerikStratejiAjani:
    def __init__(self, veri_dosyasi="hafiza_ve_analiz.json"):
        self.veri_dosyasi = veri_dosyasi
        self.hafizayi_yukle()

    def hafizayi_yukle(self):
        """Ajanın geçmiş başarılı içeriklerden öğrenmesi için veri tabanı/hafıza yüklemesi."""
        if os.path.exists(self.veri_dosyasi):
            with open(self.veri_dosyasi, "r", encoding="utf-8") as f:
                self.hafiza = json.load(f)
        else:
            self.hafiza = {"basarili_trendler": [], "uretilen_icerik_sayisi": 0}

    hafizaya_kaydet = lambda self, veri: ... # Dinamik öğrenme alanı

    def urun_analiz_ve_senaryo_uret(self, urun_adi, urun_faydasi, hedef_kitle="Genel / Emekli & Ev Hanımı"):
        """
        Ürünü analiz eder ve sosyal medya için en yüksek dönüşüm getirecek 
        video senaryosu, kanca (hook) ve paylaşım metnini hazırlar.
        """
        senaryo = {
            "zaman_damgasi": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "urun": urun_adi,
            "hedef_kitle": hedef_kitle,
            "video_kancasi": f"Dikkat! {urun_adi} ile evinizde her şey değişiyor, bunu mutlaka görün!",
            "problem_tanimi": f"{urun_faydasi} konusunda artık yorulmaya son!",
            "cozum_onerisi": "TRM Ticari Ekosistem dijital vitrin güvencesiyle doğrudan kapınızda.",
            "cagirici_mesaj": "Sınırlı refah payı fırsatını kaçırmayın, hemen inceleyin!",
            "pazarlama_tonu": "Güven veren, samimi, komşu dili ve net."
        }
        
        # Hafızayı güncelle
        self.hafiza["uretilen_icerik_sayisi"] += 1
        return senaryo

    def sosyal_medya_paylasim_metni_olustur(self, senaryo, link):
        """6 ana sosyal medya grubunda (Facebook, Instagram vb.) paylaşıma hazır metin üretir."""
        metin = (
            f"* TRM TICARI EKOSISTEMI DİJİTAL VİTRİNİ *\n\n"
            f"Değerli komşularımız, {senaryo['urun']} şimdi yerel refah destekleriyle sizlerle!\n\n"
            f"* {senaryo['problem_tanimi']}\n"
            f"-> {senaryo['cozum_onerisi']}\n\n"
            f"Teknik hiçbir şeyle uğraşmadan, sistem güvencesiyle incelemek için tıklayın:\n"
            f"Link: {link}\n\n"
            f"#TRMTicari #DijitalTicaret #YerelDayanışma #E-Ticaret"
        )
        return metin

if __name__ == "__main__":
    ajan = TRMTicariIcerikStratejiAjani()
    
    # Test Ürünü
    urun = "Akıllı Pratik Mutfak Seti"
    fayda = "mutfakta saatlerce zaman harcamak"
    link = "https://www.trendurunlermarket.com"
    
    senaryo = ajan.urun_analiz_ve_senaryo_uret(urun, fayda)
    metin = ajan.sosyal_medya_paylasim_metni_olustur(senaryo, link)
    
    print("--- AJAN ÜRETİLEN STRATEJİ VE SENARYO ---")
    print(json.dumps(senaryo, indent=4, ensure_ascii=False))
    print("\n--- SOSYAL MEDYA METNİ ---")
    print(metin)
