import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

def veritabani_sifirla():
    if not os.path.exists(DB_PATH):
        print("⚠️ Veritabanı dosyası bulunamadı.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tüm sanal esnaf ve mesaj kayıtlarını temizle
    cursor.execute("DELETE FROM mesajlar")
    cursor.execute("DELETE FROM esnaflar")
    conn.commit()
    conn.close()
    
    print("🧹 Başarıyla temizlendi! Tüm sanal hesaplar ve mesaj geçmişi veritabanından silindi.")

if __name__ == "__main__":
    veritabani_sifirla()