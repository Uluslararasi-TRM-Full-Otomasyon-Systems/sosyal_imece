import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

def whatsapp_mesajlarini_hazirla():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT id, isletme, telefon, kod FROM esnaflar WHERE durum = 'GÖNDERİLDİ'")
    esnaflar = cur.fetchall()
    
    print(f"📢 Toplam {len(esnaflar)} işletme için otonom WhatsApp çarkı tetikleniyor...\n")
    
    for e in esnaflar:
        isletme = e["isletme"]
        telefon = e["telefon"]
        kod = e["kod"]
        
        # Yüksek dönüşümlü WhatsApp outreach şablonu
        mesaj = (
            f"Merhaba {isletme} ekibi! Kuşadası gençlik ve dinamik tüketici kitlesini "
            f"doğrudan dükkanınıza yönlendiren TRM Akıllı Refah sistemine dahilsiniz.\n\n"
            f"🔑 Size özel Akıllı Onay Kodunuz: *{kod}*\n"
            f"🎁 İlk 5 yönlendirilen müşteride *%0 komisyon* avantajınız aktif!\n\n"
            f"Kasada 4 haneli kodu doğrulayarak ParaPuan kazanmaya hemen başlayabilirsiniz."
        )
        
        print(f"--- [GÖNDERİM SİMÜLASYONU] ---")
        print(f"Alıcı: {isletme} ({telefon})")
        print(f"İçerik:\n{mesaj}\n")
        
    conn.close()
    print("✅ 1. Adım otonom WhatsApp hazırlık döngüsü başarıyla tamamlandı.")

if __name__ == "__main__":
    whatsapp_mesajlarini_hazirla()