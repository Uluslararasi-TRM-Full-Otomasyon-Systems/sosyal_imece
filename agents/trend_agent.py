import os
import time
import json
from datetime import datetime

class TrendProductAgent:
    def __init__(self):
        self.agent_id = "Agent-001"
        self.name = "Trend & Product Harvester"
        print(f"[{self.agent_id}] {self.name} aktif edildi.")

    def fetch_simulated_products(self):
        print(f"[{self.agent_id}] trendurunlermarket.com uzerinden simule urunler taranamyor...")
        time.sleep(1)
        
        # Simüle edilmiş ürün verileri
        mock_products = [
            {"id": "TRM-101", "title": "Akilli Dus Basligi", "price": 499.90, "margin": "serbest"},
            {"id": "TRM-102", "title": "Koseden Donen Led Isik", "price": 299.50, "margin": "yuksek"},
            {"id": "TRM-103", "title": "Mini Tasinabilir Blender", "price": 749.00, "margin": "viral"}
        ]
        
        os.makedirs("data", exist_ok=True)
        with open("data/scraped_products.json", "w", encoding="utf-8") as f:
            json.dump(mock_products, f, ensure_ascii=False, indent=4)
            
        print(f"[{self.agent_id}] 3 adet trend urun basariyla tarandi ve data/scraped_products.json dosyasina kaydedildi.")
        return mock_products

if __name__ == "__main__":
    agent = TrendProductAgent()
    agent.fetch_simulated_products()
