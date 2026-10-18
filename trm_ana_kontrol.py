import subprocess
import os
import sys

def orkestra_calistir():
    print("==================================================")
    print("🚀 TRM ULUSLARARASI FULL OTOMASYON ANA KONTROL MERKEZİ")
    print("==================================================\n")
    
    moduller = [
        ("1. Otonom WhatsApp Çarkı", "whatsapp_otomasyon.py"),
        ("2. ParaPuan Sadakat Havuzu", "parapuan_havuz.py"),
        ("3. SMDA Medya Fabrikası", "smda_medya_fabrikasi.py"),
        ("4. AI Güvenlik Ajanı (Anti-Cheat)", "trm_guvenlik_ajani.py")
    ]
    
    for baslik, dosya in moduller:
        print(f"▶️ [{baslik}] Tetikleniyor...")
        try:
            subprocess.run([sys.executable, dosya], check=True)
        except Exception as e:
            print(f"⚠️ {baslik} çalıştırılırken hata: {e}")
        print("-" * 50)
        
    print("\n🎉 TÜM EKOSİSTEM ÇARKLARI BAŞARIYLA DÖNDÜ!")

if __name__ == "__main__":
    orkestra_calistir()