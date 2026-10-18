import sqlite3
import os
import random

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

yeni_isyerleri = [
    ("Elite Saç Tasarım", "905321112233", "Türkmen Mah. Turgut Özal Bulvarı No:14, Kuşadası/Aydın"),
    ("Venus Güzellik Merkezi", "905332223344", "Hacıfeyzullah Mah. Ege Cad. No:28, Kuşadası/Aydın"),
    ("Karizma Erkek Kuaförü", "905343334455", "Camikebir Mah. Adaletsokak No:5, Kuşadası/Aydın"),
    ("Serap Estetik & Bakım", "905354445566", "Değirmendere Mah. Kahramanlar Cad. No:11, Kuşadası/Aydın"),
    ("Trend Saç Stüdyosu", "905365556677", "Türkmen Mah. Sahil Siteleri Yolu No:7, Kuşadası/Aydın"),
    ("Bella Vita Güzellik", "905376667788", "İkiçeşmelik Mah. Candan Tarhan Blv. No:33, Kuşadası/Aydın"),
    ("10 Numara Erkek Kuaför", "905387778899", "Ege Mah. Süleyman Demirel Bulvarı No:88, Kuşadası/Aydın"),
    ("Lalezar Bayan Kuaförü", "905398889900", "Cumhuriyet Mah. Kahramanlar Cad. No:19, Kuşadası/Aydın"),
    ("Sahil Güzellik Salonu", "905301122334", "Türkmen Mah. Atatürk Bulvarı No:104, Kuşadası/Aydın"),
    ("Prestij Kuaför ve Barbershop", "905312233445", "Camikebir Mah. Eski Çarşı İçii No:3, Kuşadası/Aydın"),
    ("Zirve Saç Tasarım", "905323344556", "Hacıfeyzullah Mah. İsmet İnönü Bulvarı No:50, Kuşadası/Aydın"),
    ("Gül Kuaför Salonu", "905334455667", "Yavansu Mah. Dilek Yolu Cad. No:12, Kuşadası/Aydın"),
    ("Royal Güzellik ve Yaşam", "905345566778", "Türkmen Mah. Ege Bulvarı No:41, Kuşadası/Aydın"),
    ("Anemon Bayan Kuaförü", "905356677889", "İkiçeşmelik Mah. 500. Sokak No:8, Kuşadası/Aydın"),
    ("Modern Erkek Bakım Evi", "905367788990", "Ege Mah. Şevki Efendi Sok. No:15, Kuşadası/Aydın"),
    ("Nazar Güzellik Salonu", "905378899001", "Camikebir Mah. Kahramanlar Cad. No:22, Kuşadası/Aydın")
]

def ekle():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    eklenen_sayisi = 0
    for isletme, telefon, adres in yeni_isyerleri:
        kod = f"TRM-{random.randint(1000, 9999)}"
        try:
            cur.execute("""
                INSERT INTO esnaflar (isletme, telefon, kod, adres, durum, durum_kilit)
                VALUES (?, ?, ?, ?, 'GÖNDERİLDİ', 0)
            """, (isletme, telefon, kod, adres))
            eklenen_sayisi += 1
        except Exception as e:
            print(f"Hata ({isletme}): {e}")
            
    conn.commit()
    conn.close()
    print(f"✅ Başarıyla {eklenen_sayisi} yeni işyeri eklendi. Toplam hedef tamamlandı!")

if __name__ == "__main__":
    ekle()