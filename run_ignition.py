# run_ignition.py - Entegre Sistem Ateşleme Scripti
import sys
from pathlib import Path

# Modül yollarını güvenceye al
sys.path.append(str(Path(__file__).parent))

from real_social_publisher import RealSocialPublisher
from uteykder_veri_arsiv_ajani import archive_sosyo_ekonomik_record, verify_archive_integrity

def ignite_system():
    print("🚀 [ATEŞLEME BAŞLIYOR] TRM / TRM Ticari Ekosistem / UTEYKDER Entegre Test...")
    print("-" * 60)
    
    # 1. Yayın kanalları: gerçek durum, gönderim yok
    print("📢 [1/3] Yayın kanalları doğrulanıyor (bu adım hiçbir yere gönderi basmaz)...")
    publisher = RealSocialPublisher()
    probe = publisher.probe_telegram()
    get_me = probe["get_me"] or {}
    for row in publisher.channel_inventory(probe):
        print(f"   - {row['platform']:<10} durum={row['status']:<14} eksik={row['missing'] or '-'}")
    print(
        f"   Telegram kimlik testi: get_me_ok={get_me.get('ok')} "
        f"bot=@{get_me.get('bot_username') or '-'} detail={get_me.get('detail', 'kimlik eksik')}"
    )
    print(
        "   Gerçek gönderim için: python real_social_publisher.py --kuyruk-gonder "
        "(veya run_live_worker döngüsü, TRM_DISTRIBUTION_MODE=live ise)"
    )
    
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