# run_ignition.py - Entegre Sistem Ateşleme Scripti
import sys
from pathlib import Path

# Modül yollarını güvenceye al
sys.path.append(str(Path(__file__).parent))

from agents.social_agents import dispatch_multichannel_campaign
from uteykder_veri_arsiv_ajani import archive_sosyo_ekonomik_record, verify_archive_integrity

def ignite_system():
    print("🚀 [ATEŞLEME BAŞLIYOR] TRM / Sosyal İmece / UTEYKDER Entegre Test...")
    print("-" * 60)
    
    # 1. Çok Kanallı Sosyal Kampanya Dağıtımı
    campaign_payload = {
        "title": "Trend Akıllı Bileklik & Sağlık Asistanı",
        "link": "https://trendurunlermarket.com/akilli-bileklik",
        "campaign": "Yaz-2026-Otomasyon"
    }
    print("📢 [1/3] Sosyal medya ajanları tetikleniyor...")
    social_res = dispatch_multichannel_campaign(campaign_payload)
    print(f"   Sonuç: Çoklu kanal durumu -> {social_res.get('multi_channel_status')}")
    
    # 2. UTEYKDER Sosyo-Ekonomik Arşiv Kaydı
    archive_payload = {
        "project": "SAĞLIK İÇİN ELELE",
        "beneficiaries": 150,
        "note": "Otomatik sevk ve dağıtım testi"
    }
    print("📁 [2/3] UTEYKDER arşiv ajanı yazıyor...")
    archive_res = archive_sosyo_ekonomik_record(archive_payload)
    print(f"   Sonuç: Kayıt sayısı -> {archive_res.get('record_count')}, SHA256 -> {archive_res.get('sha256')[:12]}...")
    
    # 3. Kriptografik Bütünlük Doğrulama
    print("🔒 [3/3] Manifest & Arşiv bütünlüğü doğrulanıyor...")
    integrity_res = verify_archive_integrity()
    print(f"   Doğrulama Durumu: {'✅ GEÇERLİ' if integrity_res.get('valid') else '❌ HATA'}")
    
    print("-" * 60)
    print("✨ [ATEŞLEME TAMAMLANDI] Sistem operasyonel ve veriler mühürlendi.")

if __name__ == "__main__":
    ignite_system()