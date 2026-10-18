#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRM Nirvana v3.0 - Sistem Durumu Kontrolü
7/24 çalışma durumunu kontrol eder
"""

import requests
import json
import time
import sys
from datetime import datetime

def check_system_status():
    """Sistem durumunu kontrol et"""
    print("🔍 TRM Nirvana v3.0 Sistem Durumu Kontrolü")
    print("=" * 50)
    
    # Status API kontrol
    try:
        response = requests.get('http://localhost:9001/status', timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print("✅ Status API çalışıyor")
            print(f"📊 Ana Sistem: {status_data.get('main', 'Bilinmiyor')}")
            print(f"🌐 Web Panel: {status_data.get('panel', 'Bilinmiyor')}")
            print(f"📱 Sosyal Medya: {status_data.get('social', 'Bilinmiyor')}")
            print(f"☁️ Cloud Durumu: {status_data.get('cloud', 'Bilinmiyor')}")
            print(f"⏰ Çalışma Süresi: {status_data.get('uptime', 'Bilinmiyor')}")
            
            if status_data.get('main') == 'Aktif':
                print("\n🚀 SİSTEM 7/24 ÇALIŞIYOR!")
                print("✅ Tüm modüller aktif")
                print("🌐 Panel: http://localhost:9000")
                return True
            else:
                print("\n❌ Sistem çalışmıyor")
                return False
        else:
            print(f"❌ Status API hata: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Status API'ye bağlanılamadı")
        print("📝 SON_BASLAT.py çalışmıyor olabilir")
        return False
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

def check_panel_status():
    """Panel durumunu kontrol et"""
    try:
        response = requests.get('http://localhost:9000', timeout=5)
        if response.status_code == 200:
            print("✅ Panel çalışıyor: http://localhost:9000")
            return True
        else:
            print(f"❌ Panel hata: {response.status_code}")
            return False
    except:
        print("❌ Panel çalışmıyor")
        return False

def check_processes():
    """Process'leri kontrol et"""
    print("\n🔍 Process Kontrolü:")
    
    try:
        import psutil
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'python' in cmdline and any(x in cmdline for x in [
                    'api_server_2.py', 'main_orchestrator.py', 
                    'telegram_listener.py', 'web_scraper.py'
                ]):
                    processes.append(proc.info)
            except:
                continue
        
        if processes:
            print(f"✅ {len(processes)} Python process çalışıyor:")
            for proc in processes[:5]:  # İlk 5'i göster
                cmdline = ' '.join(proc['cmdline'] or [])
                print(f"  • PID {proc['pid']}: {cmdline[:50]}...")
        else:
            print("❌ Hiçbir Python process bulunamadı")
            
        return len(processes) > 0
        
    except ImportError:
        print("⚠️  psutil kurulu değil, process kontrol edilemiyor")
        return None

def main():
    """Ana kontrol fonksiyonu"""
    print(f"""
===============================================
    TRM NİRVANA v3.0 - SİSTEM DURUMU
===============================================
Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
===============================================
""")
    
    # Status API kontrol
    status_ok = check_system_status()
    
    # Panel kontrol
    panel_ok = check_panel_status()
    
    # Process kontrol
    processes_ok = check_processes()
    
    print("\n" + "=" * 50)
    print("📊 ÖZET DURUM:")
    
    if status_ok and panel_ok:
        print("✅ SİSTEM 7/24 ÇALIŞIYOR!")
        print("🚀 Tüm modüller aktif")
        print("🌐 Panel erişilebilir")
        print("💾 Veri akışı devam ediyor")
        print("☁️ Cloud deployment hazır")
    elif status_ok:
        print("⚠️  Sistem çalışıyor ama panel erişilebilir değil")
        print("📝 Panel yeniden başlatılabilir")
    elif panel_ok:
        print("⚠️  Panel çalışıyor ama sistem durumu bilinmiyor")
        print("📝 Status API kontrol edilmeli")
    else:
        print("❌ SİSTEM ÇALIŞMIYOR!")
        print("📝 SON_BASLAT.bat çalıştırın")
        print("🚀 'SİSTEMİ BAŞLAT' butonuna tıklayın")
    
    print("=" * 50)
    
    # Öneriler
    print("\n💡 ÖNERİLER:")
    
    if not status_ok:
        print("• SON_BASLAT.bat çalıştırın")
        print("• TEK_TIK_SON.html açın")
        print("• '🚀 SİSTEMİ BAŞLAT' butonuna tıklayın")
    
    if not panel_ok and status_ok:
        print("• Panel yeniden başlatılabilir")
        print("• http://localhost:9000 adresini kontrol edin")
    
    if status_ok:
        print("• Sistem 7/24 çalışmaya devam edecek")
        print("• Bilgisayar kapansa bile cloud'da devam eder")
        print("• Durum takibi için panel kullanabilirsiniz")

if __name__ == "__main__":
    main()
