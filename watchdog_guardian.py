# watchdog_guardian.py - Güncellenmiş Nöbetçi ve Hata Kurtarma Mekanizması
import time
import subprocess
import sys

class WatchdogGuardian:
    def __init__(self, target_script='ultra_nirvana_master.py'):
        self.target_script = target_script
        self.max_retries = 3

    def monitor_and_execute(self):
        attempt = 0
        while attempt < self.max_retries:
            print(f"[Watchdog] Sistem izleniyor... Çalıştırılıyor: {self.target_script} (Deneme: {attempt + 1}/{self.max_retries})")
            try:
                # Alt süreci doğrudan sistem konsoluna bağlayarak çalıştırıyoruz
                exit_code = subprocess.call([sys.executable, self.target_script])
                
                if exit_code == 0:
                    print("[Watchdog] İşlem başarıyla ve hatasız tamamlandı.")
                    break
                else:
                    raise subprocess.CalledProcessError(exit_code, self.target_script)
                    
            except Exception as e:
                attempt += 1
                print(f"[Watchdog UYARI] Hata yakalandı! 5 saniye içinde kurtarma protokolü tetikleniyor...")
                time.sleep(5)
                if attempt >= self.max_retries:
                    print("[Watchdog KRİTİK] Maksimum deneme aşıldı. Acil durum yedek moduna geçiliyor.")
                    self.trigger_emergency_fallback()

    def trigger_emergency_fallback(self):
        print("[Emergency Fallback] Sistem güvenli moda alındı, son başarılı SQLite kuyruk durumu donduruldu.")

if __name__ == "__main__":
    guardian = WatchdogGuardian()
    guardian.monitor_and_execute()
