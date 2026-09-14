import os
import json
import time
from datetime import datetime

class FleetExecutionLoggerAgent:
    def __init__(self):
        self.agent_id = "Agent-005"
        self.name = "Fleet Execution & Audit Master"
        print(f"[{self.agent_id}] {self.name} aktif edildi.")

    def process_fleet_queue(self):
        print(f"[{self.agent_id}] data/master_fleet_queue.json taranamyor ve 1200 gorevlik filo simulasyonu baslatiliyor...")
        
        if not os.path.exists("data/master_fleet_queue.json"):
            print(f"[{self.agent_id}] HATA: Master filo kuyrugu bulunamadi! Once Agent-004 calistirilmali.")
            return

        with open("data/master_fleet_queue.json", "r", encoding="utf-8") as f:
            fleet_queue = json.load(f)

        os.makedirs("logs", exist_ok=True)
        log_file = "logs/master_fleet_execution_log.txt"

        with open(log_file, "w", encoding="utf-8") as log:
            log.write(f"--- SOSYAL IMECE MASTER FILO SIMULASYON LOGLARI ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---\n")
            
            # Performans için ilk 10 ve son 10 logu ekrana basalım, aradakileri saniyeler içinde işleyelim
            total_tasks = len(fleet_queue)
            for idx, item in enumerate(fleet_queue, 1):
                msg = f"[FLEET-EXEC] Gorev #{idx}/{total_tasks} | Hesap: {item['account_id']} | Urun: {item['title']} | Platform: {item['target_platform']} | Durum: BASARILI"
                
                # Terminali boğmamak için her 100 görevde bir ekrana bilgi verelim, loga hepsini yazalım
                if idx <= 5 or idx > total_tasks - 5 or idx % 200 == 0:
                    print(msg)
                elif idx == 6:
                    print("[FLEET-EXEC] ... (Ara gorevler yuksek hizda simule ediliyor ve loglaniyor) ...")

                log.write(msg + "\n")

        print(f"[{self.agent_id}] Toplam {total_tasks} filo gorevi basariyla simule edildi. Loglar {log_file} dosyasina kaydedildi.")

if __name__ == "__main__":
    agent = FleetExecutionLoggerAgent()
    agent.process_fleet_queue()
