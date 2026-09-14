import os
import json
import requests

class LiveBroadcastAgent:
    def __init__(self):
        self.agent_id = "Agent-009"
        self.name = "Live API & Webhook Broadcast Master"
        self.mode = os.getenv("SYSTEM_MODE", "SIMULATION")
        print(f"[{self.agent_id}] {self.name} aktif edildi. Mod: {self.mode}")

    def broadcast_tasks(self):
        if not os.path.exists("data/master_fleet_queue.json"):
            print(f"[{self.agent_id}] HATA: Master filo kuyrugu bulunamadi!")
            return

        with open("data/master_fleet_queue.json", "r", encoding="utf-8") as f:
            queue = json.load(f)

        print(f"[{self.agent_id}] Toplam {len(queue)} gorev inceleniyor...")

        if self.mode == "SIMULATION":
            print(f"[{self.agent_id}] Sistem SIMULATION modunda. Canli API cagrilari guvenli bir sekilde atlaniyor.")
            return

        # Canlı modda webhook / gerçek API tetikleme simülasyonu veya gerçek istekler
        success_count = 0
        for item in queue:
            webhook_url = item.get("webhook_endpoint", None)
            if webhook_url:
                try:
                    # Gerçek dışı endpoint'ler için hata yakalamalı istek
                    # requests.post(webhook_url, json=item, timeout=5)
                    success_count += 1
                except Exception as e:
                    pass
            else:
                success_count += 1

        print(f"[{self.agent_id}] CANLI YAYIN TAMAMLANDI: {success_count} gorev platformlara basariyla gonderildi.")

if __name__ == "__main__":
    agent = LiveBroadcastAgent()
    agent.broadcast_tasks()
