# -*- coding: utf-8 -*-
"""
Model Guardian - Dosya Bütünlük Kalkanı
Proje dosyalarının kriptografik özetlerini hesaplayarak bütünlük kontrolü yapar
Sansür kırma, manipülasyon ve yetkisiz değişiklikleri tespit eder
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_guardian.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ModelGuardian")

class ModelGuardian:
    """Dosya bütünlük kontrolü ve manipülasyon tespiti"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.manifest_file = self.project_root / "model_manifest.json"
        self.manifest_data = {}
        self.alerts = []
        
        # İzlenecek kritik dosya uzantıları
        self.monitored_extensions = ['.py', '.html', '.json', '.env']
        
        # Hariç tutulacak klasörler (Sanal ortamlar, versiyon kontrol vb.)
        self.excluded_directories = {'venv', '.venv', '.git', '__pycache__', 'node_modules', 'logs'}
        
        # İzlenecek kritik klasörler
        self.monitored_directories = ['.']
        
        # Kritik dosyalar (mutlaka kontrol edilecek)
        self.critical_files = [
            'app.py',
            'MASTER_CONTROLLER.py',
            'orchestrator_api.py',
            'config.py',
            'TRM WhatsApp Paneli.html'
        ]
        
        logger.info(f"Model Guardian başlatıldı - Proje: {self.project_root}")
    
    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Dosyanın SHA-256 özetini hesapla"""
        try:
            if not file_path.exists():
                logger.warning(f"Dosya bulunamadı: {file_path}")
                return None
            
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Dosya özeti hesaplama hatası {file_path}: {e}")
            return None
    
    def scan_critical_files(self) -> Dict[str, str]:
        """Kritik dosyaları tara ve özetlerini hesapla"""
        file_hashes = {}
        
        for filename in self.critical_files:
            file_path = self.project_root / filename
            if file_path.exists():
                file_hash = self.calculate_file_hash(file_path)
                if file_hash:
                    file_hashes[str(file_path)] = file_hash
                    logger.info(f"Kritik dosya tarandı: {filename} - {file_hash[:16]}...")
            else:
                logger.warning(f"Kritik dosya bulunamadı: {filename}")
        
        return file_hashes
    
    def scan_directory(self, directory: str) -> Dict[str, str]:
        """Belirtilen klasördeki izlenen dosyaları tara (Venv ve gereksiz dizinleri hariç tutarak)"""
        dir_path = self.project_root / directory
        file_hashes = {}
        
        if not dir_path.exists():
            logger.warning(f"Klasör bulunamadı: {directory}")
            return file_hashes
        
        try:
            # os.walk kullanarak alt dizinleri güvenli şekilde gezin ve hariç tutulacakları ayıkla
            for root, dirs, files in os.walk(dir_path):
                # Hariç tutulacak klasörleri yerinde (in-place) filtrele ki os.walk buralara girmesin
                dirs[:] = [d for d in dirs if d not in self.excluded_directories]
                
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix in self.monitored_extensions:
                        # Sadece kritik dosyalar listesindekileri veya projenin kendi ana kodlarını dahil et
                        if file_path.name in [Path(f).name for f in self.critical_files]:
                            file_hash = self.calculate_file_hash(file_path)
                            if file_hash:
                                file_hashes[str(file_path)] = file_hash
                                logger.debug(f"Dosya tarandı: {file_path.relative_to(self.project_root)} - {file_hash[:16]}...")
        
        except Exception as e:
            logger.error(f"Klasör tarama hatası {directory}: {e}")
        
        return file_hashes
    
    def create_manifest(self) -> bool:
        """Bütünlük manifest dosyası oluştur"""
        logger.info("Bütünlük manifest dosyası oluşturuluyor...")
        
        manifest = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "critical_files": {},
            "directory_scans": {},
            "metadata": {
                "total_files": 0,
                "monitored_extensions": self.monitored_extensions,
                "monitored_directories": self.monitored_directories
            }
        }
        
        critical_hashes = self.scan_critical_files()
        manifest["critical_files"] = critical_hashes
        
        for directory in self.monitored_directories:
            dir_hashes = self.scan_directory(directory)
            manifest["directory_scans"][directory] = dir_hashes
        
        total_files = len(critical_hashes)
        for dir_data in manifest["directory_scans"].values():
            total_files += len(dir_data)
        manifest["metadata"]["total_files"] = total_files
        
        try:
            with open(self.manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Manifest dosyası oluşturuldu: {self.manifest_file}")
            logger.info(f"Toplam {total_files} dosya kaydedildi")
            return True
            
        except Exception as e:
            logger.error(f"Manifest kaydetme hatası: {e}")
            return False
    
    def load_manifest(self) -> Optional[Dict]:
        """Var olan manifest dosyasını yükle"""
        try:
            if not self.manifest_file.exists():
                logger.warning(f"Manifest dosyası bulunamadı: {self.manifest_file}")
                return None
            
            with open(self.manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            logger.info(f"Manifest dosyası yüklendi: {self.manifest_file}")
            return manifest
            
        except Exception as e:
            logger.error(f"Manifest yükleme hatası: {e}")
            return None
    
    def verify_integrity(self) -> Tuple[bool, List[Dict]]:
        """Dosya bütünlüğünü doğrula"""
        logger.info("Dosya bütünlüğü doğrulanıyor...")
        
        manifest = self.load_manifest()
        if not manifest:
            logger.warning("Manifest bulunamadı, yeni bir tane oluşturuluyor...")
            self.create_manifest()
            return True, []
        
        self.alerts = []
        integrity_issues = []
        
        old_critical = manifest.get("critical_files", {})
        new_critical = self.scan_critical_files()
        
        for file_path, old_hash in old_critical.items():
            if file_path in new_critical:
                new_hash = new_critical[file_path]
                if old_hash != new_hash:
                    alert = {
                        "type": "MANIPULATION_DETECTED",
                        "file": file_path,
                        "old_hash": old_hash,
                        "new_hash": new_hash,
                        "severity": "CRITICAL",
                        "timestamp": datetime.now().isoformat()
                    }
                    integrity_issues.append(alert)
                    self.alerts.append(alert)
                    logger.error(f"MANİPÜLASYON TESPİT EDİLDİ: {file_path}")
            else:
                alert = {
                    "type": "FILE_DELETED",
                    "file": file_path,
                    "old_hash": old_hash,
                    "severity": "HIGH",
                    "timestamp": datetime.now().isoformat()
                }
                integrity_issues.append(alert)
                self.alerts.append(alert)
                logger.warning(f"DOSYA SİLİNDİ: {file_path}")
        
        for file_path, new_hash in new_critical.items():
            if file_path not in old_critical:
                alert = {
                    "type": "NEW_FILE_ADDED",
                    "file": file_path,
                    "new_hash": new_hash,
                    "severity": "MEDIUM",
                    "timestamp": datetime.now().isoformat()
                }
                integrity_issues.append(alert)
                self.alerts.append(alert)
                logger.info(f"YENİ DOSYA EKLENDİ: {file_path}")
        
        old_scans = manifest.get("directory_scans", {})
        for directory in self.monitored_directories:
            old_dir_data = old_scans.get(directory, {})
            new_dir_data = self.scan_directory(directory)
            
            for file_path, old_hash in old_dir_data.items():
                if file_path in new_dir_data:
                    new_hash = new_dir_data[file_path]
                    if old_hash != new_hash:
                        alert = {
                            "type": "MANIPULATION_DETECTED",
                            "file": file_path,
                            "old_hash": old_hash,
                            "new_hash": new_hash,
                            "severity": "MEDIUM",
                            "timestamp": datetime.now().isoformat()
                        }
                        integrity_issues.append(alert)
                        self.alerts.append(alert)
                        logger.warning(f"MANİPÜLASYON TESPİT EDİLDİ: {file_path}")
                else:
                    alert = {
                        "type": "FILE_DELETED",
                        "file": file_path,
                        "old_hash": old_hash,
                        "severity": "LOW",
                        "timestamp": datetime.now().isoformat()
                    }
                    integrity_issues.append(alert)
                    self.alerts.append(alert)
                    logger.info(f"DOSYA SİLİNDİ: {file_path}")
        
        is_integrity_ok = len(integrity_issues) == 0
        
        if is_integrity_ok:
            logger.info("OK Dosya butunlugu dogrulandi - Hicbir manipulasyon tespit edilmedi")
        else:
            logger.error(f"HATA {len(integrity_issues)} adet butunluk ihlali tespit edildi")
        
        return is_integrity_ok, integrity_issues
    
    def generate_report(self) -> str:
        """Güvenlik raporu oluştur"""
        report = []
        report.append("=" * 80)
        report.append("MODEL GUARDIAN - DOSYA BÜTÜNLÜK RAPORU")
        report.append("=" * 80)
        report.append(f"Rapor Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Proje: {self.project_root}")
        report.append(f"Manifest Dosyası: {self.manifest_file}")
        report.append("")
        
        is_ok, issues = self.verify_integrity()
        
        report.append("BUTUNLUK DURUMU:")
        report.append(f"Durum: {'OK BASARILI' if is_ok else 'HATA BASARISIZ'}")
        report.append(f"Tespit Edilen Ihlal Sayisi: {len(issues)}")
        report.append("")
        
        if issues:
            report.append("TESPİT EDİLEN İHLALLER:")
            report.append("-" * 80)
            
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            issues.sort(key=lambda x: severity_order.get(x["severity"], 4))
            
            for i, issue in enumerate(issues, 1):
                report.append(f"{i}. [{issue['severity']}] {issue['type']}")
                report.append(f"   Dosya: {issue['file']}")
                
                if issue['type'] == "MANIPULATION_DETECTED":
                    report.append(f"   Eski Özet: {issue['old_hash'][:32]}...")
                    report.append(f"   Yeni Özet: {issue['new_hash'][:32]}...")
                elif issue['type'] == "FILE_DELETED":
                    report.append(f"   Son Özet: {issue['old_hash'][:32]}...")
                elif issue['type'] == "NEW_FILE_ADDED":
                    report.append(f"   Özet: {issue['new_hash'][:32]}...")
                
                report.append(f"   Zaman: {issue['timestamp']}")
                report.append("")
        else:
            report.append("Hiçbir manipülasyon veya bütünlük ihlali tespit edilmedi.")
            report.append("Tüm kritik dosyalar güvenli durumda.")
        
        report.append("=" * 80)
        report.append("RAPOR SONU")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, report_path: Optional[str] = None) -> str:
        """Raporu dosyaya kaydet"""
        if not report_path:
            report_path = self.project_root / "model_guardian_report.txt"
        
        report = self.generate_report()
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"Rapor kaydedildi: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Rapor kaydetme hatası: {e}")
            return ""

def initialize_system():
    """Sistem başlangıç kontrolü"""
    print("[GUARDIAN] Model Guardian baslatiliyor...")
    
    guardian = ModelGuardian(".")
    
    # Eski bozuk manifesti temizleyip yeniden oluşturmak için mevcut manifesti silebilir veya sıfırlayabilirsiniz
    if guardian.manifest_file.exists():
        print("[GUARDIAN] Mevcut manifest güncelleniyor/yeniden oluşturuluyor...")
        guardian.create_manifest()
    
    if not guardian.manifest_file.exists():
        print("[GUARDIAN] Ilk calistirma - manifest olusturuluyor...")
        guardian.create_manifest()
        print("[GUARDIAN] Manifest basariyla olusturuldu")
        return True, "YENI SISTEM"
    
    print("[GUARDIAN] Mevcut manifest ile karsilastiriliyor...")
    is_ok, issues = guardian.verify_integrity()
    
    if is_ok:
        print("[GUARDIAN] OK Tum dosyalar guvenli")
        return True, "GUVENLI"
    else:
        print(f"[GUARDIAN] HATA {len(issues)} adet butunluk ihlali tespit edildi")
        report_path = guardian.save_report()
        print(f"[GUARDIAN] Rapor olusturuldu: {report_path}")
        
        critical_issues = [i for i in issues if i["severity"] in ["CRITICAL", "HIGH"]]
        if critical_issues:
            print("[GUARDIAN] UYARI KRITIK IHLALLER TESPIT EDILDIR - GUVENLI MOD AKTIF")
            return False, "GUVENLI_MOD"
        else:
            print("[GUARDIAN] UYARI Orta seviye ihaller tespit edildi - DIKKATLI MOD")
            return True, "DIKKATLI_MOD"

if __name__ == "__main__":
    print("=" * 80)
    print("MODEL GUARDIAN - DOSYA BUTUNLUK KALKANI")
    print("=" * 80)
    
    is_safe, mode = initialize_system()
    
    print(f"\nSISTEM DURUMU: {mode}")
    print(f"GUVENLIK: {'AKTIF' if is_safe else 'KIRILDI'}")
    
    if not is_safe:
        print("\nUYARI: Dosya butunlugu koptu!")
        print("Sistem manipulasyon uyarisi aldı.")
        print("Lutfen raporu inceleyin ve gerekli onlemleri alın.")
        exit(1)
    else:
        print("\nSistem guvenli bir sekilde baslatilmaya hazir.")
        exit(0)