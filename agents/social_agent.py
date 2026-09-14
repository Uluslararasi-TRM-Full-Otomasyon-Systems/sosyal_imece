import os
import json
import time

class SocialQueueAgent:
    def __init__(self):
        self.agent_id = "Agent-002"
        self.name = "Social Media Queue & Distribution Master"
        print(f"[{self.agent_id}] {self.name} aktif edildi.")

    def build_queue(self):
        print(f"[{self.agent_id}] data/scraped_products.json okunuyor ve sosyal medya kuyrugu olusturuluyor...")
        
        if not os.path.exists("data/scraped_products.json"):
            print(f"[{self.agent_id}] HATA: Urun verisi bulunamadi! Once Agent-001 calistirilmali.")
            return

        with open("data/scraped_products.json", "r", encoding="utf-8") as f:
            products = json.load(f)

        queue = []
        platforms = ["YouTube Shorts", "TikTok", "Instagram Reels", "Facebook"]

        for prod in products:
            for platform in platforms:
                queue_item = {
                    "product_id": prod["id"],
                    "title": prod["title"],
                    "price": prod["price"],
                    "target_platform": platform,
                    "status": "queued",
                    "simulation_note": "100 hesapli ag uzerinden paylasim icin hazir"
                }
                queue.append(queue_item)

        os.makedirs("data", exist_ok=True)
        with open("data/social_queue.json", "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=4)

        print(f"[{self.agent_id}] Toplam {len(queue)} adet paylasim gorevi kuyruga eklendi ve data/social_queue.json dosyasina yazildi.")

if __name__ == "__main__":
    agent = SocialQueueAgent()
    agent.build_queue()
