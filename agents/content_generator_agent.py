import os
import json

class ContentVariationAgent:
    def __init__(self):
        self.agent_id = "Agent-007"
        self.name = "Multi-Platform Content Variation Engine"
        print(f"[{self.agent_id}] {self.name} aktif edildi.")

    def generate_variations(self):
        if not os.path.exists("data/master_fleet_queue.json"):
            print(f"[{self.agent_id}] HATA: Master filo kuyrugu bulunamadi!")
            return

        with open("data/master_fleet_queue.json", "r", encoding="utf-8") as f:
            queue = json.load(f)

        for item in queue:
            platform = item.get("target_platform", "")
            title = item.get("title", "")
            
            # Platforma özel viral kancalar ve metin optimizasyonu
            if platform == "YouTube Shorts":
                item["formatted_caption"] = f"🔥 {title} Kesinlikle görmelisin! Link profilde. #shorts #viral #trend"
            elif platform == "TikTok":
                item["formatted_caption"] = f"Bunu arıyordunuz! 🚀 {title} #fyp #tiktokturkey #trendurun"
            elif platform == "Instagram Reels":
                item["formatted_caption"] = f"✨ Tarzınızı değiştirecek: {title} 🛒 Detaylar ve sipariş için biyografideki linke tıklayın! #reels #kesfet"
            else: # Facebook
                item["formatted_caption"] = f"Kampanyalı Ürün: {title} - Avantajlı fiyatıyla hemen inceleyin! 🛍️"

        with open("data/master_fleet_queue.json", "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=4)

        print(f"[{self.agent_id}] 1200 gorev icin platform bazli ozel aciklama ve hashtag varyasyonlari olusturuldu.")

if __name__ == "__main__":
    agent = ContentVariationAgent()
    agent.generate_variations()
