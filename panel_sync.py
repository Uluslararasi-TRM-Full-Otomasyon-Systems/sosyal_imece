#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TRM NIRVANA v3.0 - Panel Synchronizer
HTML panelindeki ajan sayısını otomatik günceller ve log tutar

@author: Mehmet - TRM NIRVANA Ekibi
@version: 1.0.0
"""

import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# ============================================================
# KONFİGÜRASYON
# ============================================================

CONFIG = {
    "panel_file": "TRM Ticari Ekosistem Sistemi Yönetim ve Denetim paneli.html",
    "backup_dir": "backups",
    "log_file": "panel_sync.log",
    "new_agent_count": 200,
    "old_agent_count": 165,
    "auto_backup": True
}

# ============================================================
# LOGGING YAPILANDIRMASI
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["log_file"], encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PanelSync")

# ============================================================
# PANEL SENKRONİZASYON SINIFI
# ============================================================

class PanelSynchronizer:
    """HTML panelini senkronize eden ana sınıf"""
    
    def __init__(self, panel_path: Optional[str] = None):
        self.panel_path = Path(panel_path or CONFIG["panel_file"])
        self.backup_dir = Path(CONFIG["backup_dir"])
        self.new_count = CONFIG["new_agent_count"]
        self.old_count = CONFIG["old_agent_count"]
        self._content: Optional[str] = None
        self._changes: list = []
        
        # Backup dizinini oluştur
        if CONFIG["auto_backup"]:
            self.backup_dir.mkdir(exist_ok=True)
    
    def load_panel(self) -> bool:
        """Panel HTML dosyasını yükle"""
        if not self.panel_path.exists():
            logger.error(f"❌ Panel dosyası bulunamadı: {self.panel_path}")
            return False
        
        try:
            with open(self.panel_path, 'r', encoding='utf-8') as f:
                self._content = f.read()
            logger.info(f"✅ Panel yüklendi: {self.panel_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Panel yükleme hatası: {e}")
            return False
    
    def create_backup(self) -> bool:
        """Yedekleme oluştur"""
        if not CONFIG["auto_backup"] or not self._content:
            return True
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"panel_backup_{timestamp}.html"
        
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(self._content)
            logger.info(f"✅ Yedek oluşturuldu: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Yedekleme hatası: {e}")
            return False
    
    def update_agent_count(self) -> bool:
        """
        HTML'deki ajan sayısını güncelle
        - maxAjan değişkeni
        - Aktif Ajan gösterimi
        - Weather bilgisi
        - Agent grid başlığı
        - DNP buton metni
        """
        if not self._content:
            return False
        
        changes = []
        original_content = self._content
        
        # 1. maxAjan değişkenini güncelle
        patterns = [
            (r'let maxAjan = \d+;', f'let maxAjan = {self.new_count};'),
            (r'maxAjan = \d+;', f'maxAjan = {self.new_count};'),
            (r'"maxAjan":\s*\d+', f'"maxAjan": {self.new_count}'),
        ]
        
        for pattern, replacement in patterns:
            if re.search(pattern, self._content):
                self._content = re.sub(pattern, replacement, self._content)
                changes.append(f"maxAjan: {self.old_count} → {self.new_count}")
                break
        
        # 2. Aktif Ajan sayısını güncelle (stat-card)
        patterns = [
            (r'<div class="sayi" id="aktifAjan">\d+</div>', f'<div class="sayi" id="aktifAjan">{self.new_count}</div>'),
            (r'id="aktifAjanDetay".*?>\d+</div>', f'id="aktifAjanDetay" style="font-size:24px;color:#ffdd99;">{self.new_count}</div>'),
            (r'id="weatherAjanSayisi">\d+</span>', f'id="weatherAjanSayisi">{self.new_count}</span>'),
            (r'🤖 \d+ Ajan Kontrol', f'🤖 {self.new_count} Ajan Kontrol'),
        ]
        
        for pattern, replacement in patterns:
            if re.search(pattern, self._content):
                self._content = re.sub(pattern, replacement, self._content)
                changes.append(f"Aktif Ajan gösterimi güncellendi: {self.new_count}")
        
        # 3. DNP buton metnini güncelle
        pattern = r'🤖 DNP AJANI \(\d+\. Ajan\)'
        replacement = f'🤖 DNP AJANI ({self.new_count}. Ajan)'
        if re.search(pattern, self._content):
            self._content = re.sub(pattern, replacement, self._content)
            changes.append(f"DNP buton metni güncellendi: {self.new_count}. Ajan")
        
        # 4. Sistem sağlığı ve matris başlığını güncelle
        pattern = r'Sistem Sağlığı ve Ajan Durum Matrisi \(\d+ Ajan\)'
        replacement = f'Sistem Sağlığı ve Ajan Durum Matrisi ({self.new_count} Ajan)'
        if re.search(pattern, self._content):
            self._content = re.sub(pattern, replacement, self._content)
            changes.append(f"Matris başlığı güncellendi: {self.new_count} Ajan")
        
        # 5. Log Akışı başlangıç mesajını güncelle
        pattern = r'\[Sistem başlatıldı\] - \d+ ajan hazır'
        replacement = f'[Sistem başlatıldı] - {self.new_count} ajan hazır'
        if re.search(pattern, self._content):
            self._content = re.sub(pattern, replacement, self._content)
            changes.append(f"Log akışı başlangıç mesajı güncellendi: {self.new_count} ajan")
        
        # Değişiklikleri kaydet
        if self._content != original_content:
            self._changes = changes
            logger.info(f"✅ {len(changes)} değişiklik yapıldı:")
            for change in changes:
                logger.info(f"   - {change}")
            return True
        else:
            logger.warning("⚠️ Hiçbir değişiklik yapılmadı. Sayılar zaten güncel olabilir.")
            return False
    
    def save_panel(self) -> bool:
        """Güncellenmiş paneli kaydet"""
        if not self._content:
            return False
        
        try:
            with open(self.panel_path, 'w', encoding='utf-8') as f:
                f.write(self._content)
            logger.info(f"✅ Panel kaydedildi: {self.panel_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Panel kaydetme hatası: {e}")
            return False
    
    def write_system_log(self) -> bool:
        """
        Sistem bilgisi kısmına log olarak değişiklik bilgisini ekler
        HTML'deki log-area veya logAkis alanına ekleme yapar
        """
        if not self._content:
            return False
        
        # Log mesajını oluştur
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] 🔄 SİSTEM GÜNCELLEMESİ: Ajan sayısı {self.old_count} → {self.new_count} olarak güncellendi. ({len(self._changes)} değişiklik)"
        
        # log-area içine ekle (eğer varsa)
        pattern = r'(<div class="log-area" id="logArea">)(.*?)(</div>)'
        replacement = rf'\1{log_message}<br>\2\3'
        
        if re.search(pattern, self._content, re.DOTALL):
            self._content = re.sub(pattern, replacement, self._content, flags=re.DOTALL)
            logger.info(f"✅ Sistem log'u eklendi: {log_message}")
            return True
        
        # Alternatif: logAkis alanına ekle
        pattern = r'(<div id="logAkis".*?>)(.*?)(</div>)'
        if re.search(pattern, self._content, re.DOTALL):
            self._content = re.sub(pattern, rf'\1{log_message}<br>\2\3', self._content, flags=re.DOTALL)
            logger.info(f"✅ Sistem log'u logAkis alanına eklendi")
            return True
        
        logger.warning("⚠️ Log alanı bulunamadı, log eklenemedi.")
        return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Güncelleme raporu oluştur"""
        return {
            "timestamp": datetime.now().isoformat(),
            "old_agent_count": self.old_count,
            "new_agent_count": self.new_count,
            "changes": self._changes,
            "change_count": len(self._changes),
            "status": "success" if self._changes else "no_changes",
            "panel_file": str(self.panel_path),
            "backup_created": CONFIG["auto_backup"]
        }
    
    def run(self) -> Dict[str, Any]:
        """
        Ana çalıştırma fonksiyonu
        Tüm adımları sırayla çalıştırır
        """
        logger.info("🚀 Panel Synchronizer başlatılıyor...")
        logger.info(f"📊 Mevcut ajan sayısı: {self.old_count} → Yeni: {self.new_count}")
        
        # 1. Panel'i yükle
        if not self.load_panel():
            return {"status": "error", "message": "Panel yüklenemedi"}
        
        # 2. Yedek oluştur
        if CONFIG["auto_backup"]:
            self.create_backup()
        
        # 3. Ajan sayısını güncelle
        if not self.update_agent_count():
            return {"status": "no_changes", "message": "Değişiklik gerekmiyor"}
        
        # 4. Sistem log'u ekle
        self.write_system_log()
        
        # 5. Panel'i kaydet
        if not self.save_panel():
            return {"status": "error", "message": "Panel kaydedilemedi"}
        
        # 6. Rapor oluştur
        report = self.generate_report()
        logger.info(f"✅ Panel Synchronizer tamamlandı! {len(self._changes)} değişiklik yapıldı.")
        
        return report

# ============================================================
# KOMUT SATIRI ÇALIŞTIRMA
# ============================================================

def main():
    """Ana çalıştırma fonksiyonu"""
    synchronizer = PanelSynchronizer()
    result = synchronizer.run()
    
    print("\n" + "="*50)
    print("📊 PANEL SENKRONİZASYON RAPORU")
    print("="*50)
    print(f"📁 Dosya: {result.get('panel_file', 'Bilinmiyor')}")
    print(f"📈 Eski Ajan Sayısı: {synchronizer.old_count}")
    print(f"📈 Yeni Ajan Sayısı: {synchronizer.new_count}")
    print(f"🔄 Değişiklik Sayısı: {result.get('change_count', 0)}")
    print(f"📊 Durum: {result.get('status', 'Bilinmiyor')}")
    print("-"*50)
    
    if result.get('changes'):
        print("✅ Yapılan Değişiklikler:")
        for change in result['changes']:
            print(f"   • {change}")
    
    print("="*50)
    
    if result.get('status') == 'success':
        print("🎉 Panel başarıyla güncellendi!")
    elif result.get('status') == 'no_changes':
        print("ℹ️ Panel zaten güncel, değişiklik yapılmadı.")
    else:
        print("❌ Hata oluştu! Lütfen log dosyasını kontrol edin.")

if __name__ == "__main__":
    main()