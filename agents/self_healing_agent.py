import os
import json
from datetime import datetime

class SelfHealingAgent:
    def __init__(self):
        self.agent_id = "Agent-012"
        self.name = "Self-Healing & Data Integrity Auditor"
        print(f"[{self.agent_id}] {self.name} aktif edildi.")

    def audit_and_heal(self):
        targets = [
            "data/scraped_products.json",
            "data/social_queue.json",
            "data/master_fleet_queue.json"
        ]

        healed_count = 0
        for path in targets:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        json.load(f)
                except Exception as e:
                    print(f"[{self.agent_id}] HATA TESPIT EDILDI ({path}): {e}. Onariliyor...")
                    # Bozuk veya boş dosyayı güvenli şablonla onar
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump([], f, ensure_ascii=False, indent=4)
                    healed_count += 1
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=4)

        print(f"[{self.agent_id}] Veri butunlugu taramasi tamamlandi. Onarilan dosya sayisi: {healed_count}")
        print(f"[{self.agent_id}] Sistem mikron duzeyinde hata direncine kavustu.")

if __name__ == "__main__":
    agent = SelfHealingAgent()
    agent.audit_and_heal()
