import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

def medya_fabrikasi_calistir():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Esnaflardan rastgele 3 tanesini seçip medya üretimi simülasyonu yapalım
    cur.execute("SELECT isletme, kod FROM esnaflar LIMIT 3")
    secilenler = cur.fetchall()
    
    print("🎨 SMDA Otonom İçerik Fabrikası Çalıştırılıyor...\n")
    
    for esnaf in secilenler:
        isletme = esnaf["isletme"]
        kod = esnaf["kod"]
        
        # Otonom Reels/Shorts Metin ve Taslak Üretimi
        reels_metni = (
            f"✨ Kuşadası'nda Tarzını Yenile! ✨\n"
            f"@{isletme} kalitesiyle tanışın. TRM Onay Kodunuz: {kod} ile "
            f"ilk ziyaretinizde fırsatları yakalayın, ParaPuan kazanın!\n\n"
            f"#Kuşadası #Tarz #Güzellik #Trend #TRMTicari"
        )
        
        print(f"--- [OTONOM MEDYA PAKETİ] ---")
        print(f"Hedef İşletme: {isletme}")
        print(f"Oluşturulan Dikey Video/Reels Metni:\n{reels_metni}\n")
        
    conn.close()
    print("✅ 3. Adım SMDA Otonom İçerik Fabrikası başarıyla tamamlandı.")

if __name__ == "__main__":
    medya_fabrikasi_calistir()