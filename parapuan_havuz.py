import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

def tabloyu_olustur_ve_test_et():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # ParaPuan Havuz Tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parapuan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri_tel TEXT,
            puan REAL DEFAULT 0.0,
            harcanan REAL DEFAULT 0.0,
            son_islem TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Örnek bir müşteriye başlangıç puanı yükleme (Cross-merchant Lock-in simülasyonu)
    ornek_tel = "905551234567"
    cur.execute("SELECT puan FROM parapuan WHERE musteri_tel = ?", (ornek_tel,))
    kayit = cur.fetchone()
    
    if not kayit:
        cur.execute("INSERT INTO parapuan (musteri_tel, puan) VALUES (?, ?)", (ornek_tel, 150.0))
        print(f"🎁 Yeni Müşteri ({ornek_tel}) için 150 ParaPuan havuzda tanımlandı!")
    else:
        print(f"🔄 Müşteri mevcut ParaPuan bakiyesi: {kayit[0]} puan.")
        
    conn.commit()
    conn.close()
    print("✅ 2. Adım ParaPuan Ecosystem Lock-in altyapısı ve tablosu aktif!")

if __name__ == "__main__":
    tabloyu_olustur_ve_test_et()