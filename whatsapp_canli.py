import sqlite3
import os
import pywhatkit as pwk

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

def derya_canli_mesaj_gonder():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Gönderim bekleyen ilk esnafı seçiyoruz
    cur.execute("SELECT id, isletme, telefon, kod FROM esnaflar WHERE durum = 'GÖNDERİLDİ' LIMIT 1")
    esnaf = cur.fetchone()
    
    if not esnaf:
        print("❌ Gönderim yapılacak uygun işletme bulunamadı.")
        conn.close()
        return

    isletme = esnaf["isletme"]
    telefon = f"+{esnaf['telefon']}"
    kod = esnaf["kod"]
    
    # Derya'nın Doğal İnsan Üslubu
    mesaj = (
        f"Merhaba {isletme} yetkilisi, iyi günler dilerim! 👋\n\n"
        f"Ben Derya. Kuşadası'ndaki genç ve dinamik müşteri kitlesini doğrudan dükkanınıza yönlendiren "
        f"TRM Akıllı Refah sisteminden ulaşıyorum size.\n\n"
        f"Sistemde kaydınızı aktif ettik. Size özel tanımladığımız Akıllı Onay Kodunuz: *{kod}*\n"
        f"Ayrıca ilk 5 yönlendireceğimiz müşteride sizden *%0 komisyon* alıyoruz, yani tamamen ücretsiz deneyebilirsiniz.\n\n"
        f"Sistemin kullanımıyla ilgili aklınıza takılan bir şey olursa doğrudan buradan bana yazabilirsiniz, yardımcı olmaktan memnuniyet duyarım. 😊"
    )
    
    print(f"👩‍💼 Derya mesajı hazırladı, WhatsApp Web üzerinden gönderiliyor...")
    print(f"Alıcı: {isletme} ({telefon})")
    
    try:
        pwk.sendwhatmsg_instantly(
            phone_no=telefon, 
            message=mesaj, 
            wait_time=15, 
            tab_close=True
        )
        print(f"✅ Derya'nın mesajı {isletme} işletmesine başarıyla iletildi!")
    except Exception as e:
        print(f"⚠️ Gönderim sırasında hata: {e}")
        
    conn.close()

if __name__ == "__main__":
    derya_canli_mesaj_gonder()