import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

def mesaj_tablosu_olustur():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Derya ve esnaf arasındaki canlı sohbet geçmişi tablosu
    cur.execute('''
        CREATE TABLE IF NOT EXISTS mesajlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            esnaf_id INTEGER,
            gonderen TEXT,  -- 'ESNAF' veya 'DERYA'
            mesaj TEXT,
            tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (esnaf_id) REFERENCES esnaflar (id)
        )
    ''')
    
    conn.commit()
    print("✅ 'mesajlar' tablosu veritabanına başarıyla eklendi!")
    
    # Test amaçlı ilk esnafımıza örnek sohbet verisi ekleyelim
    cur.execute("SELECT id, isletme FROM esnaflar LIMIT 1")
    esnaf = cur.fetchone()
    
    if esnaf:
        esnaf_id = esnaf[0]
        isletme = esnaf[1]
        
        # Derya'nın attığı mesaj ve esnafın cevabı simülasyonu
        cur.execute("INSERT INTO mesajlar (esnaf_id, gonderen, mesaj) VALUES (?, 'DERYA', ?)",
                    (esnaf_id, f"Merhaba {isletme} yetkilisi, ben Derya. Sistem kaydınız açıldı!"))
        cur.execute("INSERT INTO mesajlar (esnaf_id, gonderen, mesaj) VALUES (?, 'ESNAF', ?)",
                    (esnaf_id, "Bu sistem ücretli mi acaba?"))
        cur.execute("INSERT INTO mesajlar (esnaf_id, gonderen, mesaj) VALUES (?, 'DERYA', ?)",
                    (esnaf_id, "İlk 5 müşteride %0 komisyon avantajınız aktif!"))
        
        conn.commit()
        print(f"💬 '{isletme}' için örnek mesaj geçmişi başarıyla işlendi.")
        
    conn.close()

if __name__ == "__main__":
    mesaj_tablosu_olustur()