import os
import json
import time
from datetime import datetime

class ExecutionLoggerAgent:
    def __init__(self):
        self.agent_id = "Agent-003"
        self.name = "Execution & Simulation Logger"
        print(f"[{self.agent_id}] {self.name} aktif edildi.")

    def process_queue(self):
        print(f"[{self.agent_id}] data/social_queue.json okunuyor ve simulasyon baslatiliyor...")
        
        if not os.path.exists("data/social_queue.json"):
            print(f"[{self.agent_id}] HATA: Kuyruk dosyasi bulunamadi! Once Agent-002 calistirilmali.")
            return

        with open("data/social_queue.json", "r", encoding="utf-8") as f:
            queue = json.load(f)

        os.makedirs("logs", exist_ok=True)
        log_file = "logs/execution_log.txt"

        with open(log_file, "w", encoding="utf-8") as log:
            log.write(f"--- SOSYAL IMECE SIMULASYON LOGLARI ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---\n")
            
            for idx, item in enumerate(queue, 1):
                time.sleep(0.2) # Simülasyon gecikmesi
                msg = f"[EXEC] Gorev #{idx} -> Urun: {item['title']} | Platform: {item['target_platform']} | Durum: BASARILI (Simulasyon)"
                print(msg)
                log.write(msg + "\n")

        print(f"[{self.agent_id}] Tum gorevler simule edildi. Loglar logs/execution_log.txt dosyasina kaydedildi.")

if __name__ == "__main__":
    agent = ExecutionLoggerAgent()
    agent.process_queue()
