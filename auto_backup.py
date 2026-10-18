#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Otomatik Masaüstü Yedekleme Betiği
Projenin güncel halini yedekler/ klasörüne zaman damgalı ZIP olarak alır
"""

import os
import zipfile
import shutil
from datetime import datetime
from pathlib import Path
import logging

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoBackup:
    def __init__(self, project_path: str = None):
        if project_path is None:
            # Scriptin çalıştığı dizini proje dizini olarak al
            self.project_path = Path(__file__).parent.resolve()
        else:
            self.project_path = Path(project_path).resolve()
        
        self.backup_dir = self.project_path / "yedekler"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Dışlanacak dosyalar ve klasörler
        self.exclude_patterns = [
            "__pycache__",
            ".git",
            "venv",
            ".venv",
            "node_modules",
            ".deps_v5",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
            "*.log",
            "*.pid",
            ".DS_Store",
            "Thumbs.db",
            "yedekler",  # Yedekler klasörünü kendisini yedekleme
            "backup_agents",
            "arsiv"
        ]
    
    def should_exclude(self, path: Path) -> bool:
        """
        Dosya veya klasörün dışlanması gerekip gerekmediğini kontrol et
        """
        # Dosya adını kontrol et
        for pattern in self.exclude_patterns:
            if pattern.startswith("*"):
                # Wildcard pattern
                if path.name.lower().endswith(pattern.replace("*", "")):
                    return True
            else:
                # Tam eşleşme veya klasör adı
                if pattern in path.parts or path.name == pattern:
                    return True
        
        return False
    
    def create_backup(self) -> str:
        """
        Proje yedeğini oluştur
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"trm_tam_yedek_{timestamp}.zip"
        backup_path = self.backup_dir / backup_name
        
        logger.info(f"[BACKUP] Yedekleme başlatılıyor: {backup_name}")
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.project_path):
                    # Dışlanacak klasörleri dizin listesinden çıkar
                    dirs[:] = [d for d in dirs if not self.should_exclude(Path(root) / d)]
                    
                    for file in files:
                        file_path = Path(root) / file
                        
                        if not self.should_exclude(file_path):
                            # Dosyayı ZIP'e ekle (proje dizinine göre relatif path)
                            arcname = file_path.relative_to(self.project_path)
                            zipf.write(file_path, arcname)
                            logger.debug(f"[OK] Eklendi: {arcname}")
            
            # Dosya boyutunu al
            file_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            
            logger.info(f"[OK] Yedekleme tamamlandı: {backup_name}")
            logger.info(f"[INFO] Dosya boyutu: {file_size:.2f} MB")
            logger.info(f"[DIR] Konum: {backup_path}")
            
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"[ERROR] Yedekleme hatası: {e}")
            raise
    
    def cleanup_old_backups(self, keep_count: int = 10):
        """
        Eski yedekleri temizle (son keep_count kadar yedek tut)
        """
        backups = sorted(self.backup_dir.glob("trm_tam_yedek_*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if len(backups) > keep_count:
            for old_backup in backups[keep_count:]:
                try:
                    old_backup.unlink()
                    logger.info(f"[DELETE] Eski yedek silindi: {old_backup.name}")
                except Exception as e:
                    logger.warning(f"[WARN] Yedek silinemedi {old_backup.name}: {e}")
    
    def get_backup_info(self) -> dict:
        """
        Mevcut yedekler hakkında bilgi döndür
        """
        backups = list(self.backup_dir.glob("trm_tam_yedek_*.zip"))
        
        return {
            "backup_dir": str(self.backup_dir),
            "total_backups": len(backups),
            "backups": [
                {
                    "name": b.name,
                    "size_mb": b.stat().st_size / (1024 * 1024),
                    "created": datetime.fromtimestamp(b.stat().st_mtime).isoformat()
                }
                for b in sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True)
            ]
        }

# Ana çalıştırma
if __name__ == "__main__":
    import sys
    
    try:
        backup = AutoBackup()
        
        # Yedek oluştur
        backup_path = backup.create_backup()
        
        # Eski yedekleri temizle (son 10 yedek tut)
        backup.cleanup_old_backups(keep_count=10)
        
        # Yedek bilgilerini göster
        info = backup.get_backup_info()
        print(f"\n[INFO] Yedek Bilgileri:")
        print(f"Toplam Yedek: {info['total_backups']}")
        print(f"Yedek Klasörü: {info['backup_dir']}")
        
        if info['backups']:
            print(f"\nSon Yedekler:")
            for b in info['backups'][:5]:
                print(f"  - {b['name']} ({b['size_mb']:.2f} MB) - {b['created']}")
        
        print(f"\n[OK] İşlem başarıyla tamamlandı!")
        
    except Exception as e:
        logger.error(f"[ERROR] Yedekleme başarısız: {e}")
        sys.exit(1)
