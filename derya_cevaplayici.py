import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

# Derya'nın Esnaftan Gelen Mesajlara Otonom Yanıt Kuralları (AI Mantığı)
YANIT_SENARYOLARI = {
    "ucret": (
        "Sistemimiz ilk 5 müşteri yönlendirmesinde tamamen ücretsizdir (%0 komisyon). "
        "Memnun kalırsanız sonrasında da sadece kazandığınızda işleyen komisyon modeliyle devam ediyoruz. 😊"
    ),
    "nasil": (
        "Çok basit! Müşteriniz dükkanınıza geldiğinde size özel verdiğimiz 4 haneli kodu "
        "kasa panelinden doğruluyorsunuz. Müşteri ParaPuan kazanıyor, siz de yeni müşteri kazanmış oluyorsunuz. 👍"
    ),
    "kod": (
        "Akıllı Onay Kodunuz size özel üretilmiş 4 haneli koda denir. "
        "Müşterilerinizin harcamasını doğrulayıp ParaPuan tanımlamanız için kullanılır."
    ),
    "tamam": (
        "Harika! Kaydınız aktif edilmiştir. İlk müşterileriniz yönlendirildiğinde "
        "sizi bilgilendireceğim. Bol kazançlar dilerim! 🌸"
    )
}

def derya_otonom_yanitla(gelen_mesaj, isletme_adi="İşletme"):
    gelen_mesaj_lower = gelen_mesaj.lower()
    
    # Mesaj içeriğine göre en uygun yanıtı seçme
    if any(kelime in gelen_mesaj_lower for kelime in ["ücret", "fiyat", "maliyet", "paralı"]):
        cevap = YANIT_SENARYOLARI["ucret"]
    elif any(kelime in gelen_mesaj_lower for kelime in ["nasıl", "nasil", "kullanım", "calisir"]):
        cevap = YANIT_SENARYOLARI["nasil"]
    elif any(kelime in gelen_mesaj_lower for kelime in ["kod", "onay"]):
        cevap = YANIT_SENARYOLARI["kod"]
    elif any(kelime in gelen_mesaj_lower for kelime in ["tamam", "olur", "katılıyorum", "evet", "ok"]):
        cevap = YANIT_SENARYOLARI["tamam"]
    else:
        cevap = (
            f"Notunuzu aldım {isletme_adi} yetkilisi. Konuyu hemen ekibime iletiyorum, "
            f"kısa süre içinde size detaylı bilgi sunacağım. Aklınıza takılan başka bir şey var mıydı? 😊"
        )
        
    return cevap

if __name__ == "__main__":
    print("==================================================")
    print("👩‍💼 DERYA OTONOM CEVAPLAYICI AI MOTORU TESTİ")
    print("==================================================\n")
    
    # Örnek esnaf soruları simülasyonu
    ornek_mesajlar = [
        "Bu sistem ücretli mi acaba?",
        "Kodu nasıl kullanacağız tam olarak?",
        "Tamam olur katılalım",
        "Detaylı bilgi verir misiniz?"
    ]
    
    for msg in ornek_mesajlar:
        yanit = derya_otonom_yanitla(msg, "Ender Dahan Kuaför")
        print(f"📩 Esnaf: '{msg}'")
        print(f"💬 Derya: '{yanit}'\n" + "-"*40)