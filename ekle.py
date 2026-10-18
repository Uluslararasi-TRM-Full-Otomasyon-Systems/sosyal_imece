import sqlite3
import os

path = os.path.join(os.getcwd(), 'trm_veritabani.db')
conn = sqlite3.connect(path)

# Tablo yoksa oluştur
conn.execute('''
CREATE TABLE IF NOT EXISTS esnaflar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isletme TEXT,
    telefon TEXT,
    kod TEXT UNIQUE,
    durum TEXT
)
''')

# Eski test kaydı varsa silip sıfırdan ekleyelim
conn.execute("DELETE FROM esnaflar WHERE kod = 'TRM-TEST01'")

conn.execute('''
INSERT INTO esnaflar (isletme, telefon, kod, durum) 
VALUES ('Test Isletmesi', '905300000000', 'TRM-TEST01', 'onayli')
''')

conn.commit()
conn.close()

print("✅ TEST KAYDI BAŞARIYLA YENİLENDİ!")