# -*- coding: utf-8 -*-
import os
from core.dpapi_vault import ProtectedLocalVault

def setup_dpapi_vault():
    print("🔒 Windows DPAPI Güvenli Kasa Tam Mühürleme Başlatılıyor...")
    
    # Sistemin aradığı tüm live ve auth değişkenlerini eksiksiz tanımlıyoruz
    keys_data = {
        "GEMINI_API_KEY": "AQ.Ab8RN6KPbtrPnXyy2z3MgdWhjoi",
        "GROQ_API_KEY": "gsk_AoGnqcIoCmqlW",
        "TELEGRAM_BOT_TOKEN": "8895295102:AAGDd",
        "TELEGRAM_CHAT_ID": "123456789",  # Gerekli eşik kontrolü için
        "CEO_API_KEY": "trm-secur",
        "TRM_AUTONOMOUS_DISTRIBUTION_ENABLED": "1",
        "TRM_MAGAZA_API_ENABLED": "1",
        "TRM_STORE_SIMULATE": "0",
        "TRM_STORE_API_BASE_URL": "https://magazanolsun.com/api",
        "TRM_STORE_ACCESS_TOKEN": "trm-mock-token-live",
        "TRM_DISTRIBUTION_MODE": "live"
    }
    
    try:
        vault = ProtectedLocalVault.from_default_location()
        if vault.exists():
            vault.destroy()
            vault = ProtectedLocalVault.from_default_location()
            
        vault.enroll(environment=keys_data)
        print("✅ Başarılı! Tüm sistem değişkenleri ve anahtarlar Windows DPAPI kasasına mühürlendi.")
        print("🚀 Artık 'python run_live_worker.py' komutuyla sistemi sorunsuz başlatabilirsiniz.")
            
    except Exception as e:
        print(f"❌ Kasa mühürleme hatası: {e}")

if __name__ == "__main__":
    setup_dpapi_vault()