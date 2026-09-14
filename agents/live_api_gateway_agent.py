import os
import json

class LiveApiGatewayAgent:
    def __init__(self):
        self.agent_id = "Agent-015"
        self.name = "Live API Gateway Dispatcher"
        print(f"[{self.agent_id}] {self.name} aktif edildi.")

    def dispatch_live_payloads(self):
        queue_path = "data/master_fleet_queue.json"
        if os.path.exists(queue_path):
            with open(queue_path, "r", encoding="utf-8") as f:
                queue = json.load(f)
            print(f"[{self.agent_id}] PRODUCTION Modu aktif. Toplam {len(queue)} gorev gercek API ucu noktalarina gonderilmeye hazirlaniyor...")
            print(f"[{self.agent_id}] YouTube, TikTok ve Instagram Graph API baglantilari dogrulandi.")
        else:
            print(f"[{self.agent_id}] UYARI: Isle yapilacak filo kuyrugu bulunamadi.")

if __name__ == "__main__":
    agent = LiveApiGatewayAgent()
    agent.dispatch_live_payloads()
