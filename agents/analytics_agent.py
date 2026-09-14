import os
import json
from datetime import datetime

class AnalyticsAgent:
    def __init__(self):
        self.agent_id = "Agent-010"
        self.name = "Affiliate Revenue & Performance Analytics"
        print(f"[{self.agent_id}] {self.name} aktif edildi.")

    def generate_report(self):
        if not os.path.exists("data/master_fleet_queue.json"):
            print(f"[{self.agent_id}] HATA: Kuyruk verisi bulunamadi!")
            return

        with open("data/master_fleet_queue.json", "r", encoding="utf-8") as f:
            queue = json.load(f)

        total_accounts = len(set(item.get("account_id") for item in queue))
        total_products = len(set(item.get("product_id") for item in queue))
        
        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_active_accounts": total_accounts,
            "total_products_marketed": total_products,
            "total_syndicated_posts": len(queue),
            "estimated_daily_reach": len(queue) * 250, # Her post için ortalama erişim tahmini
            "status": "Optimizasyon icin hazir"
        }

        os.makedirs("data/reports", exist_ok=True)
        report_path = "data/reports/daily_performance_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=4)

        print(f"[{self.agent_id}] Günlük performans ve gelir raporu olusturuldu: {report_path}")
        print(f"[{self.agent_id}] Özet -> Hesap: {total_accounts} | Ürün: {total_products} | Toplam Görev: {len(queue)}")

if __name__ == "__main__":
    agent = AnalyticsAgent()
    agent.generate_report()
