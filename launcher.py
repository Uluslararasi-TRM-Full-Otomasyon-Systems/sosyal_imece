#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
launcher.py - AGI Masaüstü Otomasyon Mühendisi
Çoklu ajan ekosistemini ekranda canlı olarak ayağa kaldıran otomasyon scripti

Özellikler:
- 6 temel ajanı (Elif, Amara, Lucia, Sophie, Emma, Yuki) başlatır
- Her ajan için ayrı terminal/cmd penceresi açar
- Pencere başlıklarını ajan isimleriyle eşleştirir
- 2 satır x 3 sütun (6 zone) grid yerleşimi yapar
- Log ve mesaj bus takibi sağlar
"""

import os
import sys
import json
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime

try:
    import pygetwindow as gw
    from screeninfo import get_monitors
except ImportError:
    print("⚠️ Gerekli kütüphaneler yükleniyor...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pygetwindow", "screeninfo"], check=True)
    import pygetwindow as gw
    from screeninfo import get_monitors


class AgentLauncher:
    def __init__(self, config_file="agent_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.agents = self.config.get("agents", [])
        self.grid_layout = self.config.get("grid_layout", {})
        self.inter_agent_bus = self.config.get("inter_agent_bus", {})
        self.processes = {}
        self.windows = {}
        
        print(f"🚀 [Launcher] AGI Masaüstü Otomasyon Başlatılıyor...")
        print(f"📋 [Config] {len(self.agents)} ajan yüklendi")
        
    def load_config(self):
        """agent_config.json dosyasını okur"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ [HATA] {self.config_file} dosyası bulunamadı!")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ [HATA] JSON parse hatası: {e}")
            sys.exit(1)
    
    def ensure_inter_agent_bus(self):
        """logs/inter_agent_bus.jsonl dosyasının varlığını sağlar"""
        log_file = self.inter_agent_bus.get("log_file", "logs/inter_agent_bus.jsonl")
        log_path = Path(log_file)
        
        if not log_path.parent.exists():
            log_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"📁 [Log] {log_path.parent} klasörü oluşturuldu")
        
        if not log_path.exists():
            log_path.touch()
            print(f"📝 [Log] {log_file} dosyası oluşturuldu")
        else:
            print(f"✅ [Log] {log_file} dosyası zaten mevcut")
        
        return log_path
    
    def calculate_grid_zones(self):
        """Ekranı 2x3 grid bölgelerine hesaplar"""
        monitors = get_monitors()
        if not monitors:
            print("❌ [HATA] Monitör bulunamadı!")
            return None
        
        primary_monitor = monitors[0]
        screen_width = primary_monitor.width
        screen_height = primary_monitor.height
        
        # 2 satır x 3 sütun grid
        rows = 2
        cols = 3
        zone_width = screen_width // cols
        zone_height = screen_height // rows
        
        zones = []
        for row in range(rows):
            for col in range(cols):
                zone_id = row * cols + col + 1
                zone = {
                    "id": zone_id,
                    "x": col * zone_width,
                    "y": row * zone_height,
                    "width": zone_width,
                    "height": zone_height
                }
                zones.append(zone)
        
        print(f"📐 [Grid] {rows}x{cols} grid hesaplandı ({screen_width}x{screen_height})")
        print(f"📐 [Grid] Zone boyutu: {zone_width}x{zone_height}")
        
        return zones
    
    def launch_agent_window(self, agent):
        """Tek bir ajan için terminal penceresi açar"""
        agent_name = agent["name"]
        command = agent["command"]
        
        print(f"🔧 [Ajan] {agent_name} başlatılıyor...")
        
        # Windows için CMD penceresi başlatma
        if sys.platform == "win32":
            # CMD penceresi başlığı ile başlat
            cmd = f'start "{agent_name}" cmd /k "{command}"'
            process = subprocess.Popen(cmd, shell=True)
        else:
            # Linux/Mac için terminal başlatma
            cmd = f"gnome-terminal --title='{agent_name}' -- {command}"
            process = subprocess.Popen(cmd, shell=True)
        
        self.processes[agent_name] = process
        print(f"✅ [Ajan] {agent_name} başlatıldı (PID: {process.pid})")
        
        return process
    
    def arrange_windows(self, zones):
        """Ajan pencerelerini grid bölgelerine yerleştirir"""
        print(f"🎯 [Layout] Pencereler yerleştiriliyor...")
        
        # Pencerelerin açılması için bekle
        time.sleep(3)
        
        for i, agent in enumerate(self.agents):
            agent_name = agent["name"]
            zone = zones[i] if i < len(zones) else None
            
            if not zone:
                print(f"⚠️ [Layout] {agent_name} için zone bulunamadı")
                continue
            
            # Pencereyi bul
            try:
                windows = gw.getWindowsWithTitle(agent_name)
                if not windows:
                    # Başlık tam eşleşme bulamazsa, kısmi eşleşme dene
                    all_windows = gw.getAllWindows()
                    windows = [w for w in all_windows if agent_name.lower() in w.title.lower()]
                
                if windows:
                    window = windows[0]
                    # Pencereyi move ve resize
                    window.moveTo(zone["x"], zone["y"])
                    window.resizeTo(zone["width"], zone["height"])
                    window.activate()
                    
                    print(f"✅ [Layout] {agent_name} -> Zone {zone['id']} ({zone['x']},{zone['y']})")
                    self.windows[agent_name] = window
                else:
                    print(f"⚠️ [Layout] {agent_name} penceresi bulunamadı")
            except Exception as e:
                print(f"❌ [Layout] {agent_name} yerleştirme hatası: {e}")
        
        print(f"✅ [Layout] Tüm pencereler yerleştirildi")
    
    def test_inter_agent_bus(self, log_path):
        """Log ve mesaj bus takibi testi"""
        print(f"🧪 [Test] Inter-agent bus testi başlatılıyor...")
        
        # Test mesajı yaz
        test_message = {
            "timestamp": datetime.now().isoformat(),
            "source": "launcher",
            "type": "test",
            "message": "Inter-agent bus aktif ve çalışıyor",
            "status": "success"
        }
        
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(test_message, ensure_ascii=False) + "\n")
            
            print(f"✅ [Test] Test mesajı yazıldı: {log_path}")
            
            # Dosyayı okuyarak doğrula
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_line = lines[-1] if lines else None
                
                if last_line:
                    message = json.loads(last_line)
                    print(f"✅ [Test] Mesaj doğrulandı: {message['message']}")
                    return True
        except Exception as e:
            print(f"❌ [Test] Bus test hatası: {e}")
            return False
        
        return False
    
    def launch_all_agents(self):
        """Tüm ajanları başlatır"""
        print(f"\n{'='*60}")
        print(f"🚀 TÜM AJANLAR BAŞLATILIYOR")
        print(f"{'='*60}\n")
        
        # Inter-agent bus'ı hazırla
        log_path = self.ensure_inter_agent_bus()
        
        # Grid zones hesapla
        zones = self.calculate_grid_zones()
        if not zones:
            print("❌ [HATA] Grid hesaplanamadı!")
            return False
        
        # Ajanları başlat
        for agent in self.agents:
            self.launch_agent_window(agent)
            time.sleep(1)  # Her ajan arasında 1 saniye bekle
        
        print(f"\n{'='*60}")
        print(f"⏳ Pencerelerin açılması bekleniyor...")
        print(f"{'='*60}\n")
        
        # Pencereleri yerleştir
        self.arrange_windows(zones)
        
        # Inter-agent bus testi
        self.test_inter_agent_bus(log_path)
        
        print(f"\n{'='*60}")
        print(f"✅ SİSTEM AKTİF VE HAZIR")
        print(f"{'='*60}")
        print(f"📊 Aktif Ajanlar: {len(self.agents)}")
        print(f"📐 Grid Layout: 2x3")
        print(f"📝 Log Bus: {log_path}")
        print(f"{'='*60}\n")
        
        return True
    
    def cleanup(self):
        """Tüm süreçleri temizler"""
        print(f"\n🧹 [Cleanup] Süreçler temizleniyor...")
        
        for agent_name, process in self.processes.items():
            try:
                process.terminate()
                print(f"✅ [Cleanup] {agent_name} durduruldu")
            except Exception as e:
                print(f"⚠️ [Cleanup] {agent_name} durdurma hatası: {e}")


def main():
    """Ana fonksiyon"""
    try:
        launcher = AgentLauncher()
        launcher.launch_all_agents()
        
        print(f"💡 İpucu: Pencereleri yeniden düzenlemek için Ctrl+C yapın ve script'i tekrar çalıştırın")
        print(f"💡 İpucu: Tüm ajanları durdurmak için Ctrl+C yapın")
        
        # Script'i çalışır durumda tut
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n🛑 [Kullanıcı] Durdurma sinyali alındı")
            launcher.cleanup()
            print(f"👋 [Launcher] Güle güle!")
            
    except Exception as e:
        print(f"❌ [Kritik Hata] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
