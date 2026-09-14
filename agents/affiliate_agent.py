import os
import json

class AffiliateInjectorAgent:
    def __init__(self):
        self.agent_id = "Agent-006"
        self.name = "Affiliate Link & Tracking Injector"
        print(f"[{self.agent_id}] {self.name} aktif edildi.")

    def inject_links(self):
        if not os.path.exists("data/master_fleet_queue.json"):
            print(f"[{self.agent_id}] HATA: Master filo kuyrugu bulunamadi!")
            return

        with open("data/master_fleet_queue.json", "r", encoding="utf-8") as f:
            queue = json.load(f)

        for item in queue:
            account = item.get("account_id", "User-000")
            product_id = item.get("product_id", "TRM-000")
            # Dinamik affiliate takip linki oluşturuluyor
            item["affiliate_url"] = f"https://trendurunlermarket.com/urun/{product_id.lower()}?ref={account.lower()}&utm_source=sosyal_imece"

        with open("data/master_fleet_queue.json", "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=4)

        print(f"[{self.agent_id}] Tum filo gorevlerine dinamik affiliate takip linkleri basariyla enjekte edildi.")

if __name__ == "__main__":
    agent = AffiliateInjectorAgent()
    agent.inject_links()
