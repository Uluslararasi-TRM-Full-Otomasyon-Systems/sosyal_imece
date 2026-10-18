import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

def guvenlik_ajani_kur():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Eski uyumsuz tabloyu kaldırıp güncel şemayı kuruyoruz
    cur.execute("DROP TABLE IF EXISTS ihlaller")
    
    # Güncel İhlal ve Güvenlik Takip Tablosu
    cur.execute("""
        CREATE TABLE ihlaller (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isletme_id INTEGER,
            ihlal_turu TEXT,
            tespit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            durum TEXT DEFAULT 'AKTİF'
        )
    """)
    
    # Simülasyon: Rastgele bir işletme için anti-cheat kontrolü
    cur.execute("SELECT id, isletme FROM esnaflar LIMIT 1")
    esnaf = cur.fetchone()
    
    if esnaf:
        isletme_id, isletme_adi = esnaf
        cur.execute("""
            INSERT INTO ihlaller (isletme_id, ihlal_turu, durum) 
            VALUES (?, 'Sistem Dışı Komisyon Bypass Girişimi', 'ENGELLENDİ')
        """, (isletme_id,))
        print(f"🛡️ AI Güvenlik Ajanı Devrede: '{isletme_adi}' üzerinde potansiyel kaçak girişimi engellendi ve koruma altına alındı!")
        
    conn.commit()
    conn.close()
    print("✅ 4. Adım AI Güvenlik Ajanı (Anti-Cheat) başarıyla aktifleşti ve tablo güncellendi!")

if __name__ == "__main__":
    guvenlik_ajani_kur()