# nirvana_launcher.py - Ultra Nirvana Otonom Test Başlatıcı
from ultra_nirvana_agents import UltraNirvanaOrchestrator

def start_system():
    print(">>> Sosyal İmece Ultra Nirvana Sistemi Başlatılıyor...")
    orchestrator = UltraNirvanaOrchestrator()
    
    # Küresel Otonomi ve Parmak İzi Kontrolü
    orchestrator.execute_nirvana_cycle()
    print(">>> Agent-213 (Parmak İzi Maskeleme) aktif: 100 hesap güvenli modda.")
    print(">>> Agent-215 (Küresel Otonomi) devrede: Çember kilitlendi, otonom döngü çalışıyor.")

if __name__ == "__main__":
    start_system()